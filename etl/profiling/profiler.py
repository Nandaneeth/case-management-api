"""Reusable Pandas profiling for customer support case datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd
from pandas.api.types import is_categorical_dtype, is_object_dtype, is_string_dtype


VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


@dataclass(frozen=True)
class ColumnProfile:
	"""Profile values and completeness for one dataset column."""

	data_type: str
	null_count: int
	null_percentage: float
	distinct_count: int
	duplicate_count: int
	value_counts: dict[Any, int] | None = None


@dataclass(frozen=True)
class DatasetProfile:
	"""Structured profiling result for a Pandas DataFrame."""

	row_count: int
	column_count: int
	columns: dict[str, ColumnProfile]
	checks: dict[str, dict[str, Any]]

	def to_dict(self) -> dict[str, Any]:
		"""Return the profiling result as a regular dictionary."""

		return asdict(self)


def profile_dataframe(dataframe: pd.DataFrame) -> DatasetProfile:
	"""Profile row counts, completeness, uniqueness, types, and categories."""

	row_count = len(dataframe)
	column_profiles: dict[str, ColumnProfile] = {}

	for column_name in dataframe.columns:
		series = dataframe[column_name]
		null_count = int(series.isna().sum())
		non_null_values = series.dropna()
		distinct_count = int(non_null_values.nunique())
		duplicate_count = int(len(non_null_values) - distinct_count)
		value_counts = None

		if (
			is_object_dtype(series)
			or is_categorical_dtype(series)
			or is_string_dtype(series)
		):
			value_counts = series.value_counts(dropna=False).to_dict()

		column_profiles[column_name] = ColumnProfile(
			data_type=str(series.dtype),
			null_count=null_count,
			null_percentage=(null_count / row_count * 100) if row_count else 0.0,
			distinct_count=distinct_count,
			duplicate_count=duplicate_count,
			value_counts=value_counts,
		)

	return DatasetProfile(
		row_count=row_count,
		column_count=len(dataframe.columns),
		columns=column_profiles,
		checks={},
	)


def profile_customer_support_cases(dataframe: pd.DataFrame) -> DatasetProfile:
	"""Profile a case dataset and run its required domain validation checks."""

	required_columns = {"case_number", "status", "priority"}
	missing_columns = required_columns.difference(dataframe.columns)
	if missing_columns:
		missing = ", ".join(sorted(missing_columns))
		raise ValueError(f"Missing required case columns: {missing}")

	profile = profile_dataframe(dataframe)
	case_numbers = dataframe["case_number"]
	statuses = dataframe["status"]
	priorities = dataframe["priority"]
	case_number_profile = profile.columns["case_number"]

	checks = {
		"case_number_completeness": {
			"null_count": case_number_profile.null_count,
			"null_percentage": case_number_profile.null_percentage,
			"passed": case_number_profile.null_count == 0,
		},
		"case_number_uniqueness": {
			"distinct_count": case_number_profile.distinct_count,
			"duplicate_count": case_number_profile.duplicate_count,
			"passed": case_number_profile.duplicate_count == 0,
		},
		"status_valid_values": _valid_value_check(statuses, VALID_STATUSES),
		"priority_valid_values": _valid_value_check(priorities, VALID_PRIORITIES),
	}

	return DatasetProfile(
		row_count=profile.row_count,
		column_count=profile.column_count,
		columns=profile.columns,
		checks=checks,
	)


def _valid_value_check(series: pd.Series, valid_values: set[str]) -> dict[str, Any]:
	invalid_values = series.dropna()[~series.dropna().isin(valid_values)]
	distinct_invalid_values = sorted(invalid_values.unique().tolist())
	return {
		"invalid_count": int(len(invalid_values)),
		"invalid_values": distinct_invalid_values,
		"valid_values": sorted(valid_values),
		"passed": len(invalid_values) == 0,
	}


profile_dataset = profile_customer_support_cases
