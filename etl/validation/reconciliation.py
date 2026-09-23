"""Row-count reconciliation checks for the ETL pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconciliationCheck:
	"""Result of one reconciliation comparison."""

	check_name: str
	expected_value: int
	actual_value: int
	status: str

	@property
	def passed(self) -> bool:
		"""Return whether this reconciliation check passed."""

		return self.status == "passed"


@dataclass(frozen=True)
class ReconciliationResult:
	"""Structured result containing all reconciliation checks."""

	checks: tuple[ReconciliationCheck, ...]

	@property
	def passed(self) -> bool:
		"""Return whether every reconciliation check passed."""

		return all(check.passed for check in self.checks)


def reconcile_row_counts(
	source_rows: int,
	accepted_rows: int,
	rejected_rows: int,
	standardized_rows: int,
) -> ReconciliationResult:
	"""Compare source, accepted, rejected, and standardized row counts."""

	checks = (
		_reconciliation_check(
			"source_rows_equal_accepted_plus_rejected",
			source_rows,
			accepted_rows + rejected_rows,
		),
		_reconciliation_check(
			"accepted_rows_equal_standardized_rows",
			accepted_rows,
			standardized_rows,
		),
	)
	return ReconciliationResult(checks=checks)


def _reconciliation_check(
	check_name: str,
	expected_value: int,
	actual_value: int,
) -> ReconciliationCheck:
	return ReconciliationCheck(
		check_name=check_name,
		expected_value=expected_value,
		actual_value=actual_value,
		status="passed" if expected_value == actual_value else "failed",
	)
