"""Expected schema contract for Customer Support Case data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSpec:
	"""Describe the expected shape and values for one dataset column."""

	name: str
	data_type: str
	required: bool
	allowed_values: tuple[str, ...] = ()

	@property
	def nullable(self) -> bool:
		"""Return whether the column may contain null values."""

		return not self.required


CASE_SCHEMA = (
	ColumnSpec("id", "integer", required=True),
	ColumnSpec("case_number", "string", required=True),
	ColumnSpec("title", "string", required=True),
	ColumnSpec("description", "string", required=True),
	ColumnSpec("status", "string", required=True, allowed_values=(
		"open",
		"in_progress",
		"resolved",
		"closed",
	)),
	ColumnSpec("priority", "string", required=True, allowed_values=(
		"low",
		"medium",
		"high",
		"critical",
	)),
	ColumnSpec("created_at", "datetime", required=True),
	ColumnSpec("updated_at", "datetime", required=True),
)


CASE_SOURCE_SCHEMA = CASE_SCHEMA + (
	ColumnSpec("category_code", "string", required=True),
)


REFERENCE_SCHEMA = (
	ColumnSpec("category_code", "string", required=True),
	ColumnSpec("category_name", "string", required=True),
	ColumnSpec("department", "string", required=True),
)


POLICY_SCHEMA = (
	ColumnSpec("policy_id", "string", required=True),
	ColumnSpec("category_code", "string", required=True),
	ColumnSpec("policy_name", "string", required=True),
	ColumnSpec("resolution_sla_hours", "integer", required=True),
	ColumnSpec("active", "boolean", required=True),
)


POLICY_UPDATE_SCHEMA = (
	ColumnSpec("policy_id", "string", required=True),
	ColumnSpec("category_code", "string", required=True),
	ColumnSpec("policy_version", "string", required=True),
)