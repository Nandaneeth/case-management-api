"""Common interface for Pandas-based ETL source readers."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class SourceReader(ABC):
	"""Define the read operation shared by all source readers."""

	@abstractmethod
	def read(self) -> pd.DataFrame:
		"""Read the configured source and return a Pandas DataFrame."""


def validate_source_file(file_path: str | Path, file_type: str) -> Path:
	"""Return a source path or raise the standard missing-file error."""

	source_path = Path(file_path)
	if not source_path.is_file():
		raise FileNotFoundError(
			f"{file_type} source file was not found: {source_path}"
		)
	return source_path