"""Pandas-based Parquet source reader."""

from pathlib import Path

import pandas as pd

from etl.ingestion.source_reader import SourceReader, validate_source_file


class ParquetReader(SourceReader):
	"""Read a Parquet file into a Pandas DataFrame."""

	def __init__(self, file_path: str | Path):
		self.file_path = file_path

	def read(self) -> pd.DataFrame:
		source_path = validate_source_file(self.file_path, "Parquet")
		return pd.read_parquet(source_path)


def read_parquet(file_path: str | Path) -> pd.DataFrame:
	"""Read an existing Parquet source file into a Pandas DataFrame."""

	return ParquetReader(file_path).read()