"""Structured JSON Lines audit logging for ETL pipeline runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class AuditRecord:
	"""Structured summary of one ETL pipeline run."""

	run_id: str
	pipeline_name: str
	source_type: str
	source_name: str
	start_time: datetime
	end_time: datetime
	status: str
	rows_read: int
	rows_accepted: int
	rows_rejected: int
	rows_written: int
	error_message: str | None = None

	def to_dict(self) -> dict[str, object]:
		"""Return a JSON-serializable audit record."""

		record = asdict(self)
		record["start_time"] = self.start_time.isoformat()
		record["end_time"] = self.end_time.isoformat()
		return record


class AuditLogger:
	"""Append ETL audit records to a JSON Lines file."""

	def __init__(
		self,
		output_directory: str | Path = "data/audit",
		file_name: str = "audit.jsonl",
	):
		self.output_path = Path(output_directory) / file_name

	def write(self, record: AuditRecord) -> Path:
		"""Append one audit record and return the output path."""

		self.output_path.parent.mkdir(parents=True, exist_ok=True)
		with self.output_path.open("a", encoding="utf-8") as output_file:
			output_file.write(json.dumps(record.to_dict()) + "\n")
		return self.output_path


def create_audit_record(
	pipeline_name: str,
	source_type: str,
	source_name: str,
	start_time: datetime,
	end_time: datetime,
	status: str,
	rows_read: int,
	rows_accepted: int,
	rows_rejected: int,
	rows_written: int,
	error_message: str | None = None,
) -> AuditRecord:
	"""Create an audit record with a generated run ID."""

	return AuditRecord(
		run_id=str(uuid4()),
		pipeline_name=pipeline_name,
		source_type=source_type,
		source_name=source_name,
		start_time=start_time,
		end_time=end_time,
		status=status,
		rows_read=rows_read,
		rows_accepted=rows_accepted,
		rows_rejected=rows_rejected,
		rows_written=rows_written,
		error_message=error_message,
	)
