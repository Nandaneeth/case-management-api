"""Configuration-driven selection of ETL source readers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from etl.ingestion.api_reader import ApiReader
from etl.ingestion.csv_reader import CsvReader
from etl.ingestion.database_reader import DatabaseReader
from etl.ingestion.json_reader import JsonReader
from etl.ingestion.parquet_reader import ParquetReader
from etl.ingestion.source_reader import SourceReader


ReaderFactory = Callable[[Mapping[str, Any]], SourceReader]


def _required(configuration: Mapping[str, Any], name: str) -> Any:
	value = configuration.get(name)
	if value is None or (isinstance(value, str) and not value.strip()):
		raise ValueError(f"Reader configuration requires '{name}'.")
	return value


SOURCE_READER_REGISTRY: dict[str, ReaderFactory] = {
	"csv": lambda configuration: CsvReader(
		_required(configuration, "file_path")
	),
	"json": lambda configuration: JsonReader(
		_required(configuration, "file_path")
	),
	"parquet": lambda configuration: ParquetReader(
		_required(configuration, "file_path")
	),
	"database": lambda configuration: DatabaseReader(
		_required(configuration, "connection_url"),
		_required(configuration, "table_name"),
	),
	"rest_api": lambda configuration: ApiReader(
		_required(configuration, "api_url"),
		configuration.get("timeout", 10.0),
	),
}


def get_source_reader(
	source_type: str,
	configuration: Mapping[str, Any] | None = None,
	**settings: Any,
) -> SourceReader:
	"""Return the configured reader for a supported source type."""

	reader_factory = SOURCE_READER_REGISTRY.get(source_type.strip().lower())
	if reader_factory is None:
		raise ValueError(
			f"Unsupported source type '{source_type}'. "
			f"Supported types: {', '.join(SOURCE_READER_REGISTRY)}."
		)

	reader_configuration = dict(configuration or {})
	reader_configuration.update(settings)
	return reader_factory(reader_configuration)


create_source_reader = get_source_reader
