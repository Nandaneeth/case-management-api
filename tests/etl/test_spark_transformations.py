import os
import shutil

import pytest
from pyspark.sql import SparkSession

from etl.transformations.spark_operations import summarize_standardized_cases


@pytest.fixture(scope="module")
def spark() -> SparkSession:
	"""Provide a small local Spark session for transformation tests."""

	if not os.environ.get("JAVA_HOME") and shutil.which("java") is None:
		pytest.skip("PySpark tests require Java and JAVA_HOME or java on PATH")

	session = (
		SparkSession.builder.master("local[2]")
		.appName("case-management-etl-tests")
		.config("spark.ui.enabled", "false")
		.getOrCreate()
	)
	yield session
	session.stop()


def test_spark_summary_filters_nulls_deduplicates_and_aggregates(
	spark: SparkSession,
) -> None:
	dataframe = spark.createDataFrame(
		[
			("CASE-1", "open", "high", "2026-09-01 09:00:00"),
			("CASE-1", "open", "high", "2026-09-02 09:00:00"),
			("CASE-2", "resolved", "medium", "2026-09-02 10:00:00"),
			("", "open", "low", "2026-09-02 11:00:00"),
			("CASE-3", None, "low", "2026-09-02 12:00:00"),
		],
		["case_number", "status", "priority", "updated_at"],
	)

	result = summarize_standardized_cases(dataframe).collect()

	assert {(row.status, row.priority, row.case_count) for row in result} == {
		("open", "high", 1),
		("resolved", "medium", 1),
	}
	open_row = next(row for row in result if row.status == "open")
	assert str(open_row.latest_updated_at).startswith("2026-09-02 09:00:00")


def test_spark_summary_requires_standardized_case_columns(spark: SparkSession) -> None:
	dataframe = spark.createDataFrame([("CASE-1",)], ["case_number"])

	with pytest.raises(ValueError, match="missing columns"):
		summarize_standardized_cases(dataframe)
