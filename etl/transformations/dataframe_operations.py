"""Reusable Pandas transformations for valid customer support case records."""

from __future__ import annotations

import pandas as pd


PRIORITY_DESCRIPTIONS = {
	"low": "Minor issue with limited customer impact",
	"medium": "Issue requiring normal support attention",
	"high": "Significant issue requiring prompt attention",
	"critical": "Severe issue requiring immediate attention",
}


def handle_nulls(
	dataframe: pd.DataFrame,
	fill_values: dict[str, object] | None = None,
) -> pd.DataFrame:
	"""Fill configured null values without changing the input DataFrame."""

	values = {"description": ""}
	if fill_values:
		values.update(fill_values)
	return dataframe.fillna(values)


def trim_string_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Remove leading and trailing whitespace from string-like columns."""

	result = dataframe.copy()
	for column in result.select_dtypes(include=["object", "string"]).columns:
		result[column] = result[column].map(
			lambda value: value.strip() if isinstance(value, str) else value
		)
	return result


def normalize_status(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Normalize status values to lowercase, underscore-separated text."""

	result = dataframe.copy()
	result["status"] = (
		result["status"]
		.astype("string")
		.str.strip()
		.str.lower()
		.str.replace(" ", "_", regex=False)
	)
	return result


def normalize_priority(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Normalize priority values to lowercase text."""

	result = dataframe.copy()
	result["priority"] = result["priority"].astype("string").str.strip().str.lower()
	return result


def deduplicate_cases(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Keep the first record for each case number."""

	return dataframe.drop_duplicates(subset=["case_number"], keep="first").copy()


def filter_cases(
	dataframe: pd.DataFrame,
	status: str | None = None,
	priority: str | None = None,
) -> pd.DataFrame:
	"""Filter cases by optional status and priority values."""

	mask = pd.Series(True, index=dataframe.index)
	if status is not None:
		mask &= dataframe["status"].eq(status)
	if priority is not None:
		mask &= dataframe["priority"].eq(priority)
	return dataframe.loc[mask].copy()


def aggregate_cases_by_status(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Count cases and total records by status."""

	return (
		dataframe.groupby("status", dropna=False)
		.size()
		.rename("case_count")
		.reset_index()
		.sort_values("status")
		.reset_index(drop=True)
	)


def add_priority_descriptions(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Join cases to an in-memory priority description lookup."""

	lookup = pd.DataFrame(
		[
			{"priority": priority, "priority_description": description}
			for priority, description in PRIORITY_DESCRIPTIONS.items()
		]
	)
	return dataframe.merge(lookup, on="priority", how="left", validate="many_to_one")


def rank_cases_within_status(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Rank cases within each status by priority and newest update time."""

	priority_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
	result = dataframe.copy()
	result["_priority_order"] = result["priority"].map(priority_order).fillna(99)
	result["_updated_at_sort"] = pd.to_datetime(
		result["updated_at"], errors="coerce"
	)
	result["_row_order"] = range(len(result))

	result = result.sort_values(
		["status", "_priority_order", "_updated_at_sort", "_row_order"],
		ascending=[True, True, False, True],
		na_position="last",
	)
	result["status_rank"] = result.groupby("status", dropna=False).cumcount() + 1
	return result.sort_values("_row_order").drop(
		columns=["_priority_order", "_updated_at_sort", "_row_order"]
	)
