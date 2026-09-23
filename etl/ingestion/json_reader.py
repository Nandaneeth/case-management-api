"""Reusable JSON source reader for the customer support ETL pipeline."""

from pathlib import Path

import pandas as pd

from etl.ingestion.source_reader import SourceReader, validate_source_file


class JsonReader(SourceReader):
	"""Read a JSON file into a Pandas DataFrame."""

	def __init__(self, file_path: str | Path):
		self.file_path = file_path

	def read(self) -> pd.DataFrame:
		source_path = validate_source_file(self.file_path, "JSON")
		return pd.read_json(source_path)


def read_json(file_path: str | Path) -> pd.DataFrame:
	"""Read an existing JSON source file into a Pandas DataFrame."""

	return JsonReader(file_path).read()
