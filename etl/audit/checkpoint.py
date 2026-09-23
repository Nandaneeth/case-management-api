"""Local timestamp checkpoint support for incremental ETL loads."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import pandas as pd

T = TypeVar("T")


class CheckpointStore:
	"""Store and read the last successfully processed timestamp as JSON."""

	def __init__(
		self,
		checkpoint_path: str | Path = "data/audit/cases_checkpoint.json",
	):
		self.checkpoint_path = Path(checkpoint_path)

	def read(self) -> pd.Timestamp | None:
		"""Return the last processed timestamp, or None for the first run."""

		if not self.checkpoint_path.is_file():
			return None
		with self.checkpoint_path.open("r", encoding="utf-8") as checkpoint_file:
			value = json.load(checkpoint_file).get("last_processed_timestamp")
		return pd.Timestamp(value) if value else None

	def filter_new_records(
		self,
		dataframe: pd.DataFrame,
		timestamp_column: str = "updated_at",
	) -> pd.DataFrame:
		"""Return only rows newer than the stored checkpoint timestamp."""

		if timestamp_column not in dataframe.columns:
			raise ValueError(
				f"Incremental timestamp column '{timestamp_column}' is missing."
			)
		timestamps = pd.to_datetime(dataframe[timestamp_column], errors="raise")
		last_processed = self.read()
		if last_processed is None:
			return dataframe.copy()
		return dataframe.loc[timestamps > last_processed].copy()

	def update(
		self,
		dataframe: pd.DataFrame,
		timestamp_column: str = "updated_at",
	) -> None:
		"""Persist the newest timestamp after successful processing only."""

		if dataframe.empty:
			return
		if timestamp_column not in dataframe.columns:
			raise ValueError(
				f"Incremental timestamp column '{timestamp_column}' is missing."
			)
		timestamps = pd.to_datetime(dataframe[timestamp_column], errors="raise")
		latest_timestamp = timestamps.max()
		self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
		with self.checkpoint_path.open("w", encoding="utf-8") as checkpoint_file:
			json.dump(
				{"last_processed_timestamp": latest_timestamp.isoformat()},
				checkpoint_file,
			)

	def process_new_records(
		self,
		dataframe: pd.DataFrame,
		processor: Callable[[pd.DataFrame], T],
		timestamp_column: str = "updated_at",
	) -> T:
		"""Process new rows and update state only when the processor succeeds."""

		new_records = self.filter_new_records(dataframe, timestamp_column)
		result = processor(new_records)
		self.update(new_records, timestamp_column)
		return result
