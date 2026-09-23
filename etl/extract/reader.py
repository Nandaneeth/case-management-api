"""Metadata-driven source extraction for the ETL pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from etl.metadata.reader import MetadataConfiguration

logger = logging.getLogger(__name__)


class ExtractionError(FileNotFoundError):
	"""Raised when a configured source cannot be read."""


class SourceReader:
	"""Read a configured source into a Spark DataFrame."""

	def __init__(self, spark: SparkSession):
		self.spark = spark

	def read(self, configuration: MetadataConfiguration) -> DataFrame:
		"""Read the source described by metadata; CSV is supported for now."""

		table = configuration.table
		source_path = table.source_path.strip()
		if not source_path:
			raise ExtractionError("Metadata contains an empty source path.")
		if table.file_format.lower() != "csv":
			raise ValueError(
				f"Unsupported source format '{table.file_format}'. Only CSV is supported."
			)

		source = Path(source_path)
		if not source.exists():
			raise ExtractionError(
				f"Configured source file was not found: {source_path}"
			)

		logger.info("Reading CSV source %s", source_path)
		return (
			self.spark.read.format("csv")
			.option("header", True)
			.option("inferSchema", True)
			.load(source_path)
		)


def read_source(
	spark: SparkSession, configuration: MetadataConfiguration
) -> DataFrame:
	"""Read a source using its metadata configuration."""

	return SourceReader(spark).read(configuration)
