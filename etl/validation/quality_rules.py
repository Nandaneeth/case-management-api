"""Row-level quality rules for Customer Support Case records."""

from __future__ import annotations

import pandas as pd

from etl.config.case_schema import CASE_SCHEMA


INVALID_REFERENCE_CATEGORY = "INVALID_REFERENCE_CATEGORY"


def split_valid_and_rejected_records(
	dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
	"""Separate case records that pass or fail the row-level quality rules."""

	required_columns = {"case_number", "status", "priority"}
	missing_columns = required_columns.difference(dataframe.columns)
	if missing_columns:
		missing = ", ".join(sorted(missing_columns))
		raise ValueError(f"Missing required quality-rule columns: {missing}")

	case_numbers = dataframe["case_number"]
	missing_case_number = case_numbers.isna() | case_numbers.astype("string").str.strip().eq("")
	duplicate_case_number = case_numbers.duplicated(keep=False) & ~missing_case_number
	invalid_status = dataframe["status"].isna() | ~dataframe["status"].isin(
		_allowed_values("status")
	)
	invalid_priority = dataframe["priority"].isna() | ~dataframe["priority"].isin(
		_allowed_values("priority")
	)

	reasons = pd.Series("", index=dataframe.index, dtype="string")
	for mask, reason in (
		(missing_case_number, "missing case_number"),
		(duplicate_case_number, "duplicate case_number"),
		(invalid_status, "invalid status"),
		(invalid_priority, "invalid priority"),
	):
		reasons = reasons.mask(mask, reasons.where(reasons.eq(""), reasons + "; ") + reason)

	rejected_mask = reasons.ne("")
	valid_records = dataframe.loc[~rejected_mask].copy()
	rejected_records = dataframe.loc[rejected_mask].copy()
	rejected_records["rejection_reason"] = reasons.loc[rejected_mask]
	return valid_records, rejected_records


def split_valid_and_invalid_reference_categories(
	dataframe: pd.DataFrame,
	reference_dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
	"""Reject case rows whose category code is absent from reference data."""

	if "category_code" not in dataframe.columns:
		raise ValueError("Missing required referential-integrity column: category_code")
	if "category_code" not in reference_dataframe.columns:
		raise ValueError("Reference data is missing required column: category_code")

	known_categories = set(reference_dataframe["category_code"].dropna())
	valid_mask = dataframe["category_code"].isin(known_categories)
	valid_records = dataframe.loc[valid_mask].copy()
	rejected_records = dataframe.loc[~valid_mask].copy()
	if not rejected_records.empty:
		rejected_records["rejection_reason"] = INVALID_REFERENCE_CATEGORY
	return valid_records, rejected_records


def _allowed_values(column_name: str) -> tuple[str, ...]:
	"""Get allowed values for a column from the shared case contract."""

	for column in CASE_SCHEMA:
		if column.name == column_name:
			return column.allowed_values
	return ()
