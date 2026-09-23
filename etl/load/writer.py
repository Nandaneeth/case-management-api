"""Write extracted source data to the Bronze layer."""

from __future__ import annotations

import logging
from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp

logger = logging.getLogger(__name__)


class BronzeWriter:
	"""Persist raw extracted data as append-only Parquet files."""

	def __init__(self, output_path: str | Path = "data/bronze"):
		self.output_path = str(output_path)

	def write(self, dataframe: DataFrame, output_path: str | Path | None = None) -> str:
		"""Add ingestion metadata and write the DataFrame to Bronze as Parquet."""

		destination = str(output_path) if output_path is not None else self.output_path
		Path(destination).mkdir(parents=True, exist_ok=True)
		bronze_dataframe = dataframe.withColumn(
			"ingestion_timestamp", current_timestamp()
		)
		row_count = bronze_dataframe.count()
		bronze_dataframe.write.mode("append").format("parquet").save(destination)
		logger.info("Wrote %d rows to Bronze path %s", row_count, destination)
		return destination


def write_bronze(
	dataframe: DataFrame, output_path: str | Path = "data/bronze"
) -> str:
	"""Write extracted data to a configurable Bronze path."""

	return BronzeWriter(output_path).write(dataframe)
