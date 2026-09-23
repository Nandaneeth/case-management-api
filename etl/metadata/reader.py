"""Read and validate ETL metadata without performing pipeline processing."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import Row, SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


class MetadataValidationError(ValueError):
	"""Raised when required metadata is missing or incomplete."""


@dataclass(frozen=True)
class TableMetadata:
	table_metadata_id: int
	source_system: str
	source_table_name: str
	target_table_name: str
	source_path: str
	file_format: str
	target_layer: str
	target_path: str
	active_flag: bool


@dataclass(frozen=True)
class ColumnMapping:
	source_column_name: str
	target_column_name: str
	target_data_type: str
	mapping_type: str
	transformation_rule: str | None


@dataclass(frozen=True)
class Scd2Rule:
	target_table_name: str
	business_key_column: str
	change_detection_columns: tuple[str, ...]
	effective_start_column: str
	effective_end_column: str
	current_flag_column: str


@dataclass(frozen=True)
class MetadataConfiguration:
	table: TableMetadata
	column_mappings: tuple[ColumnMapping, ...]
	scd2_rule: Scd2Rule


_TABLE_SCHEMA = StructType(
	[
		StructField("table_metadata_id", IntegerType(), False),
		StructField("source_system", StringType(), False),
		StructField("source_table_name", StringType(), False),
		StructField("target_table_name", StringType(), False),
		StructField("source_path", StringType(), False),
		StructField("file_format", StringType(), False),
		StructField("target_layer", StringType(), False),
		StructField("target_path", StringType(), False),
		StructField("active_flag", IntegerType(), False),
	]
)

_MAPPING_SCHEMA = StructType(
	[
		StructField("source_column_name", StringType(), False),
		StructField("target_column_name", StringType(), False),
		StructField("target_data_type", StringType(), False),
		StructField("mapping_type", StringType(), False),
		StructField("transformation_rule", StringType(), True),
	]
)


class MetadataReader:
	"""Load one active pipeline configuration from the SQLite metadata store."""

	def __init__(self, spark: SparkSession, metadata_database_path: str | Path):
		self.spark = spark
		self.metadata_database_path = str(metadata_database_path)

	def read(self, table_metadata_id: int) -> MetadataConfiguration:
		"""Return the active table, mappings, and SCD2 rule for one configuration."""

		with sqlite3.connect(self.metadata_database_path) as connection:
			table_row = connection.execute(
				"""
				SELECT table_metadata_id, source_system, source_table_name,
					   target_table_name, source_path, file_format, target_layer,
					   target_path, active_flag
				FROM table_metadata
				WHERE table_metadata_id = ? AND active_flag = 1
				""",
				(table_metadata_id,),
			).fetchone()
			if table_row is None:
				raise MetadataValidationError(
					f"Active table metadata {table_metadata_id} was not found."
				)

			mapping_rows = connection.execute(
				"""
				SELECT source_column_name, target_column_name, target_data_type,
					   mapping_type, transformation_rule
				FROM column_mapping
				WHERE table_metadata_id = ?
				ORDER BY column_mapping_id
				""",
				(table_metadata_id,),
			).fetchall()
			rule_row = connection.execute(
				"""
				SELECT target_table_name, business_key_column,
					   change_detection_columns, effective_start_column,
					   effective_end_column, current_flag_column
				FROM scd2_rules
				WHERE table_metadata_id = ?
				""",
				(table_metadata_id,),
			).fetchone()

		if not mapping_rows:
			raise MetadataValidationError(
				f"Table metadata {table_metadata_id} has no column mappings."
			)
		if rule_row is None:
			raise MetadataValidationError(
				f"Table metadata {table_metadata_id} has no SCD2 rule."
			)

		table = self._read_table(table_row)
		mappings = self._read_mappings(mapping_rows)
		rule = Scd2Rule(
			target_table_name=rule_row[0],
			business_key_column=rule_row[1],
			change_detection_columns=tuple(
				column.strip()
				for column in rule_row[2].split(",")
				if column.strip()
			),
			effective_start_column=rule_row[3],
			effective_end_column=rule_row[4],
			current_flag_column=rule_row[5],
		)
		if not rule.change_detection_columns:
			raise MetadataValidationError(
				f"Table metadata {table_metadata_id} has no change detection columns."
			)
		return MetadataConfiguration(table, mappings, rule)

	def _read_table(self, row: tuple[object, ...]) -> TableMetadata:
		dataframe = self.spark.createDataFrame(
			[Row(**dict(zip((field.name for field in _TABLE_SCHEMA), row)))],
			_TABLE_SCHEMA,
		)
		values = dataframe.first()
		return TableMetadata(
			table_metadata_id=values.table_metadata_id,
			source_system=values.source_system,
			source_table_name=values.source_table_name,
			target_table_name=values.target_table_name,
			source_path=values.source_path,
			file_format=values.file_format,
			target_layer=values.target_layer,
			target_path=values.target_path,
			active_flag=bool(values.active_flag),
		)

	def _read_mappings(
		self, rows: list[tuple[object, ...]]
	) -> tuple[ColumnMapping, ...]:
		dataframe = self.spark.createDataFrame(
			[
				Row(**dict(zip((field.name for field in _MAPPING_SCHEMA), row)))
				for row in rows
			],
			_MAPPING_SCHEMA,
		)
		return tuple(
			ColumnMapping(
				source_column_name=row.source_column_name,
				target_column_name=row.target_column_name,
				target_data_type=row.target_data_type,
				mapping_type=row.mapping_type,
				transformation_rule=row.transformation_rule,
			)
			for row in dataframe.collect()
		)
