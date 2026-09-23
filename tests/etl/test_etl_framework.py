"""Unit tests for the local Pandas ETL framework."""

from pathlib import Path

import pandas as pd
import pytest

from etl.ingestion.csv_reader import read_csv
from etl.pipeline import PipelinePaths, run_pipeline
from etl.profiling.profiler import profile_dataset
from etl.transformations.dataframe_operations import deduplicate_cases, handle_nulls
from etl.validation.quality_rules import (
	INVALID_REFERENCE_CATEGORY,
	split_valid_and_invalid_reference_categories,
	split_valid_and_rejected_records,
)
from etl.validation.reconciliation import reconcile_row_counts
from etl.validation.schema_validator import validate_schema


def case_frame(**overrides: object) -> pd.DataFrame:
	"""Build a small valid case DataFrame with optional column overrides."""

	data = {
		"id": [1, 2],
		"case_number": ["CASE-1", "CASE-2"],
		"title": ["Password reset", "Payment failed"],
		"description": ["Reset link failed", "Card was declined"],
		"status": ["open", "resolved"],
		"priority": ["high", "medium"],
		"created_at": ["2026-09-01 09:00:00", "2026-09-01 10:00:00"],
		"updated_at": ["2026-09-01 09:00:00", "2026-09-02 10:00:00"],
	}
	data.update(overrides)
	return pd.DataFrame(data)


def test_csv_ingestion_reads_dataframe(tmp_path: Path) -> None:
	path = tmp_path / "cases.csv"
	case_frame().to_csv(path, index=False)

	result = read_csv(path)

	assert isinstance(result, pd.DataFrame)
	assert len(result) == 2


def test_csv_ingestion_rejects_missing_file(tmp_path: Path) -> None:
	with pytest.raises(FileNotFoundError, match="CSV source file was not found"):
		read_csv(tmp_path / "missing.csv")


def test_dataset_profiling_reports_counts_and_nulls() -> None:
	dataframe = case_frame(description=["Present", None])

	profile = profile_dataset(dataframe)

	assert profile.row_count == 2
	assert profile.column_count == 8
	assert profile.columns["description"].null_count == 1
	assert profile.columns["description"].null_percentage == 50.0


def test_schema_validation_accepts_expected_case_schema() -> None:
	result = validate_schema(case_frame())

	assert result.is_valid
	assert not result.failed_checks


def test_invalid_status_is_rejected() -> None:
	dataframe = case_frame(status=["pending", "open"])

	_, rejected = split_valid_and_rejected_records(dataframe)

	assert len(rejected) == 1
	assert rejected.iloc[0]["rejection_reason"] == "invalid status"


def test_invalid_priority_is_rejected() -> None:
	dataframe = case_frame(priority=["urgent", "low"])

	_, rejected = split_valid_and_rejected_records(dataframe)

	assert len(rejected) == 1
	assert rejected.iloc[0]["rejection_reason"] == "invalid priority"


def test_duplicate_case_number_is_rejected() -> None:
	dataframe = case_frame(case_number=["CASE-1", "CASE-1"])

	valid, rejected = split_valid_and_rejected_records(dataframe)

	assert valid.empty
	assert len(rejected) == 2
	assert set(rejected["rejection_reason"]) == {"duplicate case_number"}


def test_null_handling_fills_missing_description() -> None:
	dataframe = case_frame(description=[None, "Present"])

	result = handle_nulls(dataframe)

	assert result.loc[0, "description"] == ""
	assert result.loc[1, "description"] == "Present"


def test_deduplication_keeps_first_case_record() -> None:
	dataframe = pd.DataFrame(
		{"case_number": ["CASE-1", "CASE-1", "CASE-2"], "status": ["open"] * 3}
	)

	result = deduplicate_cases(dataframe)

	assert result["case_number"].tolist() == ["CASE-1", "CASE-2"]


def test_rejected_records_keep_all_applicable_reasons() -> None:
	dataframe = pd.DataFrame(
		{
			"case_number": [None, "CASE-1"],
			"status": ["pending", "bad"],
			"priority": ["urgent", "critical"],
		}
	)

	_, rejected = split_valid_and_rejected_records(dataframe)

	assert rejected.iloc[0]["rejection_reason"] == (
		"missing case_number; invalid status; invalid priority"
	)


def test_reconciliation_returns_passed_and_failed_statuses() -> None:
	passed = reconcile_row_counts(10, 8, 2, 8)
	failed = reconcile_row_counts(10, 7, 2, 8)

	assert passed.passed
	assert all(check.status == "passed" for check in passed.checks)
	assert not failed.passed
	assert all(check.status == "failed" for check in failed.checks)


def test_reference_category_check_rejects_only_invalid_codes() -> None:
	cases = pd.DataFrame(
		{"case_number": ["CASE-1", "CASE-2"], "category_code": ["CAT-001", "CAT-999"]}
	)
	reference = pd.DataFrame({"category_code": ["CAT-001"]})

	valid, rejected = split_valid_and_invalid_reference_categories(cases, reference)

	assert valid["category_code"].tolist() == ["CAT-001"]
	assert rejected["category_code"].tolist() == ["CAT-999"]
	assert rejected.iloc[0]["rejection_reason"] == INVALID_REFERENCE_CATEGORY


def test_pipeline_is_idempotent_for_same_input(tmp_path: Path) -> None:
	paths = PipelinePaths(
		input_path=tmp_path / "cases.csv",
		standardized_path=tmp_path / "standardized.parquet",
		rejected_path=tmp_path / "rejected.csv",
		curated_path=tmp_path / "curated.parquet",
		checkpoint_path=tmp_path / "checkpoint.json",
		enrichment_enabled=False,
	)
	case_frame().to_csv(paths.input_path, index=False)

	first = run_pipeline(paths)
	first_standardized = pd.read_parquet(paths.standardized_path)
	first_curated = pd.read_parquet(paths.curated_path)
	second = run_pipeline(paths)
	second_standardized = pd.read_parquet(paths.standardized_path)
	second_curated = pd.read_parquet(paths.curated_path)

	assert first.rows_written == 2
	assert second.pipeline_status == "completed_no_new_records"
	pd.testing.assert_frame_equal(first_standardized, second_standardized)
	pd.testing.assert_frame_equal(first_curated, second_curated)


def test_pipeline_joins_case_reference_policy_and_api_sources(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	paths = PipelinePaths(
		input_path=tmp_path / "cases.csv",
		reference_path=tmp_path / "reference.csv",
		policy_metadata_path=tmp_path / "policy.csv",
		policy_api_url="http://mock-policy-api/policy-updates",
		standardized_path=tmp_path / "standardized.parquet",
		rejected_path=tmp_path / "rejected.csv",
		curated_path=tmp_path / "curated.parquet",
		checkpoint_path=tmp_path / "checkpoint.json",
	)
	cases = pd.concat([case_frame(), case_frame().iloc[[0]]], ignore_index=True)
	cases["case_number"] = ["CASE-1", "CASE-2", "CASE-3"]
	cases["category_code"] = ["CAT-001", "CAT-003", "CAT-999"]
	cases.to_csv(paths.input_path, index=False)
	pd.DataFrame(
		[
			{
				"category_code": "CAT-001",
				"category_name": "Account Access",
				"department": "Identity and Access",
			},
			{
				"category_code": "CAT-003",
				"category_name": "Billing and Payments",
				"department": "Billing Operations",
			},
		]
	).to_csv(paths.reference_path, index=False)
	pd.DataFrame(
		[
			{
				"policy_id": "POL-001",
				"category_code": "CAT-001",
				"policy_name": "Account Access Recovery",
				"resolution_sla_hours": 8,
				"active": True,
			},
			{
				"policy_id": "POL-003",
				"category_code": "CAT-003",
				"policy_name": "Billing Dispute Review",
				"resolution_sla_hours": 24,
				"active": True,
			},
		]
	).to_csv(paths.policy_metadata_path, index=False)
	monkeypatch.setattr(
		"etl.ingestion.api_reader.ApiReader.read",
		lambda _reader: pd.DataFrame(
			[
				{
					"policy_id": "POL-001",
					"category_code": "CAT-001",
					"policy_version": "2026.09",
				},
				{
					"policy_id": "POL-003",
					"category_code": "CAT-003",
					"policy_version": "2026.09",
				},
			]
		),
	)

	result = run_pipeline(paths)
	standardized = pd.read_parquet(paths.standardized_path)
	curated = pd.read_parquet(paths.curated_path)
	rejected = pd.read_csv(paths.rejected_path)

	assert result.rows_read == 3
	assert result.rows_accepted == 2
	assert result.rows_rejected == 1
	assert reconcile_row_counts(
		result.rows_read,
		result.rows_accepted,
		result.rows_rejected,
		result.rows_written,
	).passed
	assert set(standardized["category_code"]) == {"CAT-001", "CAT-003"}
	assert set(curated["department"]) == {"Identity and Access", "Billing Operations"}
	assert set(curated["policy_version"]) == {"2026.09"}
	assert rejected.iloc[0]["rejection_reason"] == INVALID_REFERENCE_CATEGORY
