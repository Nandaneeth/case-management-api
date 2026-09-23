"""Validate Pandas DataFrames against the Customer Support Case contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from pandas.api.types import (
	is_datetime64_any_dtype,
	is_integer_dtype,
	is_object_dtype,
	is_string_dtype,
)

from etl.config.case_schema import CASE_SCHEMA, ColumnSpec


@dataclass(frozen=True)
class ValidationCheck:
	"""Describe one schema validation check."""

	name: str
	message: str
	affected_columns: tuple[str, ...]


@dataclass(frozen=True)
class ValidationResult:
	"""Structured result containing passed and failed validation checks."""

	passed_checks: tuple[ValidationCheck, ...]
	failed_checks: tuple[ValidationCheck, ...]

	@property
	def is_valid(self) -> bool:
		"""Return True when all validation checks passed."""

		return not self.failed_checks


@dataclass(frozen=True)
class ChangedColumn:
	"""Describe a column whose observed type differs from the contract."""

	name: str
	expected_type: str
	actual_type: str


@dataclass(frozen=True)
class SchemaComparison:
	"""Structured report of schema evolution relative to the expected contract."""

	added_columns: tuple[str, ...]
	removed_columns: tuple[str, ...]
	changed_columns: tuple[ChangedColumn, ...]
	compatibility_status: str

	@property
	def is_compatible(self) -> bool:
		"""Return whether the observed schema matches the expected contract."""

		return self.compatibility_status == "compatible"


def compare_schema(
	dataframe: pd.DataFrame,
	schema: tuple[ColumnSpec, ...] = CASE_SCHEMA,
) -> SchemaComparison:
	"""Report added, removed, and type-changed columns without modifying data."""

	expected_columns = {column.name: column for column in schema}
	actual_columns = set(dataframe.columns)
	added_columns = tuple(
		column for column in dataframe.columns if column not in expected_columns
	)
	removed_columns = tuple(
		column.name for column in schema if column.name not in actual_columns
	)
	changed_columns = tuple(
		ChangedColumn(
			name=column.name,
			expected_type=column.data_type,
			actual_type=str(dataframe[column.name].dtype),
		)
		for column in schema
		if column.name in actual_columns
		and not _is_type_compatible(dataframe[column.name], column.data_type)
	)

	status = (
		"compatible"
		if not added_columns and not removed_columns and not changed_columns
		else "incompatible"
	)
	return SchemaComparison(
		added_columns=added_columns,
		removed_columns=removed_columns,
		changed_columns=changed_columns,
		compatibility_status=status,
	)


def validate_schema(
	dataframe: pd.DataFrame,
	schema: tuple[ColumnSpec, ...] = CASE_SCHEMA,
) -> ValidationResult:
	"""Validate columns, types, required values, and allowed case values."""

	passed: list[ValidationCheck] = []
	failed: list[ValidationCheck] = []

	def record(check: ValidationCheck, success: bool) -> None:
		if success:
			passed.append(check)
		else:
			failed.append(check)

	expected_columns = [column.name for column in schema]
	missing_columns = [
		column_name
		for column_name in expected_columns
		if column_name not in dataframe.columns
	]
	record(
		ValidationCheck(
			name="required_columns",
			message=(
				"All required columns are present."
				if not missing_columns
				else f"Missing required columns: {', '.join(missing_columns)}."
			),
			affected_columns=tuple(missing_columns),
		),
		not missing_columns,
	)

	for column in schema:
		if column.name not in dataframe.columns:
			continue

		series = dataframe[column.name]
		type_compatible = _is_type_compatible(series, column.data_type)
		record(
			ValidationCheck(
				name=f"data_type:{column.name}",
				message=(
					f"Column '{column.name}' has a compatible {column.data_type} type."
					if type_compatible
					else f"Column '{column.name}' is not compatible with {column.data_type}."
				),
				affected_columns=(column.name,),
			),
			type_compatible,
		)

		if column.required:
			null_count = int(series.isna().sum())
			record(
				ValidationCheck(
					name=f"required_values:{column.name}",
					message=(
						f"Required column '{column.name}' contains no null values."
						if null_count == 0
						else f"Column '{column.name}' contains {null_count} null value(s)."
					),
					affected_columns=(column.name,),
				),
				null_count == 0,
			)

		if column.allowed_values:
			invalid_values = sorted(
				series.dropna()[~series.dropna().isin(column.allowed_values)]
				.unique()
				.tolist()
			)
			record(
				ValidationCheck(
					name=f"allowed_values:{column.name}",
					message=(
						f"Column '{column.name}' contains only allowed values."
						if not invalid_values
						else f"Column '{column.name}' contains invalid value(s): {invalid_values}."
					),
					affected_columns=(column.name,),
				),
				not invalid_values,
			)

	return ValidationResult(tuple(passed), tuple(failed))


def _is_type_compatible(series: pd.Series, expected_type: str) -> bool:
	"""Allow common Pandas representations of the contract's basic types."""

	non_null = series.dropna()
	if expected_type == "integer":
		return is_integer_dtype(series) or (
			not non_null.empty
			and pd.to_numeric(non_null, errors="coerce").notna().all()
			and (pd.to_numeric(non_null) % 1 == 0).all()
		)
	if expected_type == "string":
		return is_string_dtype(series) or is_object_dtype(series)
	if expected_type == "datetime":
		return is_datetime64_any_dtype(series) or (
			not non_null.empty
			and pd.to_datetime(non_null, errors="coerce").notna().all()
		)
	return False
