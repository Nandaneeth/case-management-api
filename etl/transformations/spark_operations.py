"""Optional PySpark transformations for standardized case data."""

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


_REQUIRED_COLUMNS = {"case_number", "status", "priority", "updated_at"}


def summarize_standardized_cases(dataframe: DataFrame) -> DataFrame:
	"""Build a latest-case workload summary from standardized case records.

	The transformation is intentionally independent from the Pandas pipeline. It
	filters unusable keys, keeps the latest record per case with a window, and
	aggregates the remaining cases by status and priority.
	"""

	missing_columns = _REQUIRED_COLUMNS.difference(dataframe.columns)
	if missing_columns:
		missing = ", ".join(sorted(missing_columns))
		raise ValueError(f"Standardized case data is missing columns: {missing}")

	usable_records = dataframe.filter(
		F.col("case_number").isNotNull()
		& F.col("status").isNotNull()
		& F.col("priority").isNotNull()
		& F.length(F.trim(F.col("case_number"))) > 0
	)

	latest_window = Window.partitionBy("case_number").orderBy(
		F.to_timestamp(F.col("updated_at")).desc_nulls_last()
	)
	latest_records = (
		usable_records
		.withColumn("_updated_at", F.to_timestamp(F.col("updated_at")))
		.withColumn("_row_number", F.row_number().over(latest_window))
		.filter(F.col("_row_number") == 1)
	)

	return (
		latest_records.groupBy("status", "priority")
		.agg(
			F.count("*").alias("case_count"),
			F.max("_updated_at").alias("latest_updated_at"),
		)
		.orderBy("status", "priority")
	)
