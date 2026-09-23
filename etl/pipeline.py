"""Local batch orchestration for Customer Support Case data."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
import json
from pathlib import Path

import pandas as pd

from etl.config.case_schema import CASE_SCHEMA
from etl.audit.checkpoint import CheckpointStore
from etl.ingestion.csv_reader import read_csv
from etl.profiling.profiler import profile_dataset
from etl.transformations.dataframe_operations import (
	aggregate_cases_by_status,
	handle_nulls,
	normalize_priority,
	normalize_status,
	trim_string_columns,
)
from etl.validation.quality_rules import split_valid_and_rejected_records
from etl.validation.schema_validator import validate_schema


@dataclass(frozen=True)
class PipelineSummary:
	"""Counts and final status for one local batch run."""

	rows_read: int
	rows_accepted: int
	rows_rejected: int
	rows_written: int
	pipeline_status: str


@dataclass(frozen=True)
class PipelinePaths:
	"""Configurable input and output locations for the local pipeline."""

	input_path: Path = Path("data/raw/cases.csv")
	standardized_path: Path = Path("data/standardized/cases.parquet")
	rejected_path: Path = Path("data/rejected/cases_rejected.csv")
	curated_path: Path = Path("data/curated/case_summary.parquet")
	checkpoint_path: Path = Path("data/audit/cases_checkpoint.json")


def run_pipeline(paths: PipelinePaths = PipelinePaths()) -> PipelineSummary:
	"""Run the local CSV-to-standardized-and-curated batch pipeline."""

	raw_records = read_csv(paths.input_path)
	checkpoint = CheckpointStore(paths.checkpoint_path)
	records_to_process = checkpoint.filter_new_records(raw_records)
	rows_read = len(records_to_process)
	if records_to_process.empty:
		return PipelineSummary(0, 0, 0, 0, "completed_no_new_records")

	profile_dataset(records_to_process)
	validation_result = validate_schema(records_to_process)
	missing_column_check = next(
		(
			check
			for check in validation_result.failed_checks
			if check.name == "required_columns"
		),
		None,
	)
	if missing_column_check is not None:
		raise ValueError(missing_column_check.message)

	valid_records, rejected_records = split_valid_and_rejected_records(
		records_to_process
	)
	valid_records, schema_rejected = _reject_required_nulls(valid_records)
	rejected_records = _combine_rejected_records(rejected_records, schema_rejected)

	standardized_records = _standardize(valid_records)
	standardized_output = _merge_standardized_records(
		paths.standardized_path, standardized_records
	)
	curated_records = aggregate_cases_by_status(standardized_output)[
		["status", "case_count"]
	]

	_write_parquet(standardized_output, paths.standardized_path)
	_write_csv(rejected_records, paths.rejected_path)
	_write_parquet(curated_records, paths.curated_path)
	checkpoint.update(records_to_process)

	rows_accepted = len(standardized_records)
	rows_rejected = len(rejected_records)
	return PipelineSummary(
		rows_read=rows_read,
		rows_accepted=rows_accepted,
		rows_rejected=rows_rejected,
		rows_written=len(standardized_output),
		pipeline_status=(
			"completed_with_rejections" if rows_rejected else "completed"
		),
	)


def _standardize(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Apply the existing small transformations to accepted records."""

	result = trim_string_columns(dataframe)
	result = normalize_status(result)
	result = normalize_priority(result)
	result = handle_nulls(result)
	return result


def _merge_standardized_records(
	path: Path,
	new_records: pd.DataFrame,
) -> pd.DataFrame:
	"""Merge new rows with existing output using the logical record identity."""

	if path.is_file():
		existing_records = pd.read_parquet(path)
		combined = pd.concat([existing_records, new_records], ignore_index=True)
	else:
		combined = new_records.copy()

	combined["_logical_updated_at"] = pd.to_datetime(
		combined["updated_at"], errors="raise"
	)
	combined = combined.drop_duplicates(
		subset=["case_number", "_logical_updated_at"],
		keep="last",
	)
	return combined.drop(columns=["_logical_updated_at"])


def _reject_required_nulls(
	dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
	"""Reject rows that violate required-field nullability in the contract."""

	required_columns = [column.name for column in CASE_SCHEMA if column.required]
	null_masks = dataframe[required_columns].isna()
	rejected_mask = null_masks.any(axis=1)
	valid_records = dataframe.loc[~rejected_mask].copy()
	rejected_records = dataframe.loc[rejected_mask].copy()
	if not rejected_records.empty:
		rejected_records["rejection_reason"] = null_masks.loc[rejected_mask].apply(
			lambda row: "; ".join(
				f"missing {column}" for column, is_null in row.items() if is_null
			),
			axis=1,
		)
	return valid_records, rejected_records


def _combine_rejected_records(
	quality_rejected: pd.DataFrame,
	schema_rejected: pd.DataFrame,
) -> pd.DataFrame:
	"""Combine rejection outputs while preserving the raw record columns."""

	if quality_rejected.empty and schema_rejected.empty:
		return pd.DataFrame(columns=[*quality_rejected.columns, "rejection_reason"])
	return pd.concat([quality_rejected, schema_rejected], axis=0).copy()


def _write_parquet(dataframe: pd.DataFrame, path: Path) -> None:
	"""Write a DataFrame as Parquet and explain missing local engines clearly."""

	path.parent.mkdir(parents=True, exist_ok=True)
	try:
		dataframe.to_parquet(path, index=False)
	except ImportError as error:
		raise RuntimeError(
			"Writing Parquet requires 'pyarrow' or 'fastparquet' in the environment."
		) from error


def _write_csv(dataframe: pd.DataFrame, path: Path) -> None:
	"""Write rejected records as CSV."""

	path.parent.mkdir(parents=True, exist_ok=True)
	dataframe.to_csv(path, index=False)


if __name__ == "__main__":
	print(json.dumps(asdict(run_pipeline()), indent=2))
