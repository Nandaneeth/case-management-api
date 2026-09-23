"""Local batch orchestration for Customer Support Case data."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
import json
from pathlib import Path

import pandas as pd

from etl.config.case_schema import (
	CASE_SCHEMA,
	CASE_SOURCE_SCHEMA,
	POLICY_SCHEMA,
	POLICY_UPDATE_SCHEMA,
	REFERENCE_SCHEMA,
)
from etl.audit.checkpoint import CheckpointStore
from etl.config.source_registry import get_source_reader
from etl.profiling.profiler import profile_dataset
from etl.transformations.dataframe_operations import (
	aggregate_cases_by_status,
	handle_nulls,
	normalize_priority,
	normalize_status,
	trim_string_columns,
)
from etl.validation.quality_rules import (
	split_valid_and_invalid_reference_categories,
	split_valid_and_rejected_records,
)
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
	reference_path: Path = Path("data/raw/reference_data.csv")
	policy_metadata_path: Path = Path("data/raw/policy_metadata.csv")
	policy_api_url: str = "http://127.0.0.1:8001/api/policy-updates"
	enrichment_enabled: bool = True


def run_pipeline(paths: PipelinePaths = PipelinePaths()) -> PipelineSummary:
	"""Run the local CSV-to-standardized-and-curated batch pipeline."""

	raw_records = _standardize_case(
		get_source_reader("csv", file_path=paths.input_path).read()
	)
	checkpoint = CheckpointStore(paths.checkpoint_path)
	records_to_process = checkpoint.filter_new_records(raw_records)
	rows_read = len(records_to_process)
	if records_to_process.empty:
		return PipelineSummary(0, 0, 0, 0, "completed_no_new_records")

	profile_dataset(records_to_process)
	_validate_source_schema(
		records_to_process,
		CASE_SOURCE_SCHEMA if paths.enrichment_enabled else CASE_SCHEMA,
		"case",
	)

	valid_records, rejected_records = split_valid_and_rejected_records(
		records_to_process
	)
	valid_records, schema_rejected = _reject_required_nulls(
		valid_records,
		CASE_SOURCE_SCHEMA if paths.enrichment_enabled else CASE_SCHEMA,
	)
	rejected_records = _combine_rejected_records(rejected_records, schema_rejected)

	standardized_records = _standardize(valid_records)
	if paths.enrichment_enabled:
		reference_records = _read_and_validate_csv(
			paths.reference_path, REFERENCE_SCHEMA, "reference"
		)
		policy_records = _read_and_validate_csv(
			paths.policy_metadata_path, POLICY_SCHEMA, "policy metadata"
		)
		policy_updates = _read_and_validate_api(
			paths.policy_api_url, POLICY_UPDATE_SCHEMA, "policy updates"
		)
		standardized_records, join_rejected = _join_sources(
			standardized_records,
			reference_records,
			policy_records,
			policy_updates,
		)
		rejected_records = _combine_rejected_records(
			rejected_records, join_rejected
		)

	standardized_output = _merge_standardized_records(
		paths.standardized_path, standardized_records
	)
	if paths.enrichment_enabled:
		curated_records = _curated_columns(standardized_output)
	else:
		curated_records = aggregate_cases_by_status(standardized_output)[
			["status", "case_count"]
		]

	_reconcile_counts(
		len(records_to_process),
		len(standardized_records),
		len(rejected_records),
		len(standardized_records),
	)

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


def _standardize_case(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Normalize case source names, values, and types before validation."""

	result = _standardize_column_names(dataframe)
	result = trim_string_columns(result)
	if "status" in result.columns:
		result = normalize_status(result)
	if "priority" in result.columns:
		result = normalize_priority(result)
	if "id" in result.columns:
		result["id"] = pd.to_numeric(result["id"], errors="coerce").astype("Int64")
	for column in ("created_at", "updated_at"):
		if column in result.columns:
			result[column] = pd.to_datetime(result[column], errors="coerce")
	if "category_code" in result.columns:
		result["category_code"] = result["category_code"].astype("string").str.upper()
	return result


def _standardize_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Normalize source column names to the pipeline's snake_case contract."""

	return dataframe.rename(
		columns={
			column: str(column).strip().lower().replace(" ", "_")
			for column in dataframe.columns
		}
	).copy()


def _standardize_reference(dataframe: pd.DataFrame) -> pd.DataFrame:
	result = trim_string_columns(_standardize_column_names(dataframe))
	if "category_code" in result.columns:
		result["category_code"] = result["category_code"].astype("string").str.upper()
	return result


def _standardize_policy(dataframe: pd.DataFrame) -> pd.DataFrame:
	result = trim_string_columns(_standardize_column_names(dataframe))
	if "category_code" in result.columns:
		result["category_code"] = result["category_code"].astype("string").str.upper()
	if "resolution_sla_hours" in result.columns:
		result["resolution_sla_hours"] = pd.to_numeric(
			result["resolution_sla_hours"], errors="coerce"
		).astype("Int64")
	if "active" in result.columns:
		result["active"] = result["active"].astype("string").str.lower().map(
			{"true": True, "false": False, "1": True, "0": False}
		).astype("boolean")
	return result


def _standardize_policy_updates(dataframe: pd.DataFrame) -> pd.DataFrame:
	result = trim_string_columns(_standardize_column_names(dataframe))
	if "category_code" in result.columns:
		result["category_code"] = result["category_code"].astype("string").str.upper()
	return result


def _validate_source_schema(
	dataframe: pd.DataFrame,
	schema: tuple,
	source_name: str,
) -> None:
	"""Fail fast for structural/type errors while leaving row rejection to rules."""

	result = validate_schema(dataframe, schema)
	blocking_checks = tuple(
		check
		for check in result.failed_checks
		if check.name.startswith("required_columns")
		or check.name.startswith("data_type:")
	)
	if blocking_checks:
		raise ValueError(
			f"{source_name.title()} schema validation failed: "
			+ "; ".join(check.message for check in blocking_checks)
		)


def _read_and_validate_csv(
	path: Path,
	schema: tuple,
	source_name: str,
) -> pd.DataFrame:
	dataframe = get_source_reader("csv", file_path=path).read()
	if source_name == "reference":
		standardized = _standardize_reference(dataframe)
	else:
		standardized = _standardize_policy(dataframe)
	_validate_source_schema(standardized, schema, source_name)
	return standardized


def _read_and_validate_api(
	url: str,
	schema: tuple,
	source_name: str,
) -> pd.DataFrame:
	dataframe = get_source_reader("rest_api", api_url=url).read()
	standardized = _standardize_policy_updates(dataframe)
	_validate_source_schema(standardized, schema, source_name)
	return standardized


def _join_sources(
	cases: pd.DataFrame,
	reference: pd.DataFrame,
	policy: pd.DataFrame,
	policy_updates: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
	"""Join source datasets and reject cases with missing reference relationships."""

	valid_cases, join_rejected = split_valid_and_invalid_reference_categories(
		cases, reference
	)

	joined = valid_cases.merge(
		reference,
		on="category_code",
		how="inner",
		validate="many_to_one",
	)
	joined = joined.merge(
		policy,
		on="category_code",
		how="inner",
		validate="many_to_one",
	)
	return joined.merge(
		policy_updates[["policy_id", "policy_version"]],
		on="policy_id",
		how="left",
		validate="many_to_one",
	), join_rejected


def _curated_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
	columns = [
		"case_number", "title", "description", "status", "priority",
		"created_at", "updated_at", "category_code", "category_name",
		"department", "policy_id", "policy_name", "resolution_sla_hours",
		"active", "policy_version",
	]
	return dataframe[[column for column in columns if column in dataframe.columns]].copy()


def _reconcile_counts(
	source_rows: int,
	accepted_rows: int,
	rejected_rows: int,
	standardized_rows: int,
) -> None:
	from etl.validation.reconciliation import reconcile_row_counts

	result = reconcile_row_counts(
		source_rows, accepted_rows, rejected_rows, standardized_rows
	)
	if not result.passed:
		raise ValueError("ETL row-count reconciliation failed.")


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
	schema: tuple,
) -> tuple[pd.DataFrame, pd.DataFrame]:
	"""Reject rows that violate required-field nullability in the contract."""

	required_columns = [column.name for column in schema if column.required]
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
		columns = list(dict.fromkeys([*quality_rejected.columns, "rejection_reason"]))
		return pd.DataFrame(columns=columns)
	frames = [quality_rejected, schema_rejected]
	return pd.concat(
		[frame.loc[:, ~frame.columns.duplicated(keep="first")] for frame in frames],
		axis=0,
	).copy()


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
