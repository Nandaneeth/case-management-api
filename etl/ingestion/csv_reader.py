"""Reusable CSV source reader for the customer support ETL pipeline."""

from pathlib import Path

import pandas as pd

from etl.ingestion.source_reader import SourceReader, validate_source_file


class CsvReader(SourceReader):
	"""Read a CSV file into a Pandas DataFrame."""

	def __init__(self, file_path: str | Path):
		self.file_path = file_path

	def read(self) -> pd.DataFrame:
		source_path = validate_source_file(self.file_path, "CSV")
		return pd.read_csv(source_path)


def read_csv(file_path: str | Path) -> pd.DataFrame:
	"""Read an existing CSV source file into a Pandas DataFrame."""

	return CsvReader(file_path).read()


read_csv_source = read_csv
