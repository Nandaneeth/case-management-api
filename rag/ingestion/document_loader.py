"""Utilities for loading Markdown policy documents into structured Python objects.

This module is intentionally focused on ingestion only. It reads Markdown policy
files, extracts approved metadata fields, and preserves the full document text so
that later stages can perform chunking, indexing, or retrieval workflows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

METADATA_FIELD_MAP: dict[str, str] = {
    "policy id": "policy_id",
    "policy name": "policy_name",
    "category": "category",
    "version": "version",
    "effective date": "effective_date",
    "department": "department",
    "status": "status",
    "source": "source",
}

REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "policy_id",
    "policy_name",
    "category",
    "version",
    "effective_date",
    "department",
    "status",
    "source",
)


class PolicyDocumentError(ValueError):
    """Raised when a Markdown policy file is missing required metadata or malformed."""


@dataclass(frozen=True)
class PolicyMetadata:
    """Normalized metadata extracted from a policy document."""

    policy_id: str
    policy_name: str
    category: str
    version: str
    effective_date: str
    department: str
    status: str
    source: str

    def to_dict(self) -> dict[str, str]:
        """Return a plain dictionary representation of the document metadata."""
        return {key: getattr(self, key) for key in REQUIRED_METADATA_FIELDS}


@dataclass(frozen=True)
class PolicyDocument:
    """Represents one Markdown policy file and its metadata.

    The text field preserves the full document contents so the object can be used
    directly by later chunking or retrieval pipelines.
    """

    file_path: Path
    metadata: PolicyMetadata
    text: str

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary suitable for downstream processing pipelines."""
        return {
            "file_path": str(self.file_path),
            "metadata": self.metadata.to_dict(),
            "text": self.text,
        }


def load_policy_documents(directory: str | Path) -> list[PolicyDocument]:
    """Load all Markdown policy files from a directory.

    Args:
        directory: Directory containing policy Markdown files.

    Returns:
        A list of structured PolicyDocument objects in sorted path order.

    Raises:
        FileNotFoundError: If the supplied directory does not exist.
        NotADirectoryError: If the supplied path is not a directory.
        PolicyDocumentError: If any Markdown file is missing metadata or malformed.
    """
    policy_root = Path(directory)

    if not policy_root.exists():
        raise FileNotFoundError(f"Policy directory does not exist: {policy_root}")
    if not policy_root.is_dir():
        raise NotADirectoryError(f"Policy path is not a directory: {policy_root}")

    policy_files = sorted(policy_root.rglob("*.md"), key=lambda path: str(path))
    return [parse_policy_document(policy_file) for policy_file in policy_files]


def parse_policy_document(file_path: str | Path) -> PolicyDocument:
    """Parse a single Markdown policy file into a PolicyDocument object.

    Args:
        file_path: Path to the Markdown policy file.

    Returns:
        Structured policy representation containing metadata and full text.

    Raises:
        PolicyDocumentError: If the document cannot be parsed or required metadata is missing.
    """
    policy_file = Path(file_path)

    if not policy_file.exists():
        raise PolicyDocumentError(f"Policy file does not exist: {policy_file}")
    if policy_file.suffix.lower() != ".md":
        raise PolicyDocumentError(f"Policy file is not a Markdown document: {policy_file}")

    try:
        text = policy_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyDocumentError(f"Unable to decode Markdown file as UTF-8: {policy_file}") from exc

    if not text.strip():
        raise PolicyDocumentError(f"Policy document is empty: {policy_file}")

    metadata = _extract_metadata(text, policy_file)
    return PolicyDocument(file_path=policy_file, metadata=metadata, text=text)


def _extract_metadata(markdown_text: str, file_path: Path) -> PolicyMetadata:
    """Extract the required metadata fields from a policy document.

    The accepted schema is a simple Markdown key-value list, such as:
    '- Policy ID: POL-001' or 'Policy name: Customer Password Reset'.
    """
    metadata_values: dict[str, str] = {}
    pattern = re.compile(
        r"^\s*(?:[-*]\s*)?(?P<key>Policy ID|Policy name|Category|Version|Effective date|Department|Status|Source)\s*:\s*(?P<value>.+?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    for match in pattern.finditer(markdown_text):
        key = match.group("key").strip()
        value = match.group("value").strip()
        normalized_key = METADATA_FIELD_MAP.get(key.lower())
        if normalized_key is not None:
            metadata_values[normalized_key] = value

    missing_fields = [
        field for field in REQUIRED_METADATA_FIELDS if not metadata_values.get(field, "").strip()
    ]
    if missing_fields:
        missing_list = ", ".join(missing_fields)
        raise PolicyDocumentError(
            f"Malformed policy document '{file_path.name}': missing required metadata fields: {missing_list}"
        )

    return PolicyMetadata(**{field: metadata_values[field] for field in REQUIRED_METADATA_FIELDS})


__all__ = [
    "PolicyDocument",
    "PolicyDocumentError",
    "PolicyMetadata",
    "load_policy_documents",
    "parse_policy_document",
]
