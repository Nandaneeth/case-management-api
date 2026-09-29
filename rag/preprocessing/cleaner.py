"""Utilities for cleaning raw policy text before downstream processing.

This module is intentionally limited to text normalization and validation. It does
not perform chunking, embedding, or vector-store operations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

_METADATA_KEY_ALIASES: dict[str, str] = {
    "policy id": "policy_id",
    "policy name": "policy_name",
    "category": "category",
    "version": "version",
    "effective date": "effective_date",
    "department": "department",
    "status": "status",
    "source": "source",
}

_METADATA_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<key>Policy ID|Policy name|Category|Version|Effective date|Department|Status|Source)\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CleanedPolicyDocument:
    """Canonical representation of a cleaned policy document.

    The metadata field keeps structured policy metadata separate from the cleaned
    body text so the content can be chunked or indexed independently.
    """

    metadata: dict[str, str]
    text: str


def clean_policy_text(text: str) -> str:
    """Normalize raw policy text and reject empty or whitespace-only content.

    Args:
        text: Raw policy Markdown or plain-text content.

    Returns:
        A cleaned string with normalized line endings, collapsed whitespace, and
        reduced excessive blank lines while preserving headings and content.

    Raises:
        TypeError: If the input is not a string.
        ValueError: If the document contains no meaningful content.
    """
    if not isinstance(text, str):
        raise TypeError("Policy content must be a string.")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.strip():
        raise ValueError("Policy document is empty.")

    cleaned_lines: list[str] = []
    pending_blank = False
    last_was_heading = False

    for raw_line in normalized.split("\n"):
        line = raw_line.strip()

        if not line:
            if cleaned_lines and not pending_blank:
                pending_blank = True
                cleaned_lines.append("")
            continue

        pending_blank = False

        if line.startswith("#"):
            cleaned = re.sub(r"\s+", " ", line)
            cleaned_lines.append(cleaned)
            last_was_heading = True
            continue

        if last_was_heading and cleaned_lines and cleaned_lines[-1].startswith("#"):
            cleaned_lines.append("")
        last_was_heading = False

        cleaned = re.sub(r"\s+", " ", line)
        cleaned_lines.append(cleaned)

    cleaned_text = "\n".join(cleaned_lines).strip()
    if not cleaned_text:
        raise ValueError("Policy document is empty after cleaning.")

    return cleaned_text


def extract_policy_metadata(text: str) -> tuple[dict[str, str], str]:
    """Separate policy metadata from the body content when metadata is stored at the top.

    This helper is intentionally forgiving and only extracts simple key-value
    metadata lines that match the project’s policy metadata format.

    Args:
        text: Raw Markdown policy content.

    Returns:
        A tuple of (metadata_dict, cleaned_body_text).

    Raises:
        ValueError: If the document is empty or contains no body after metadata removal.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.strip():
        raise ValueError("Policy document is empty.")

    lines = normalized.split("\n")
    metadata: dict[str, str] = {}
    body_start_index = 0

    for index, line in enumerate(lines):
        match = _METADATA_LINE_RE.match(line)
        if not match:
            if metadata:
                body_start_index = index
                break
            body_start_index = index
            break

        key = match.group("key").strip()
        value = match.group("value").strip()
        metadata[_METADATA_KEY_ALIASES.get(key.lower(), key.lower())] = value
        body_start_index = index + 1

    body_lines = lines[body_start_index:]
    body_text = "\n".join(body_lines).strip()

    if metadata:
        if not body_text:
            raise ValueError("Policy document is missing body content after metadata removal.")
        return metadata, clean_policy_text(body_text)

    return {}, clean_policy_text(normalized)


def clean_policy_document(text: str, metadata: Mapping[str, str] | None = None) -> CleanedPolicyDocument:
    """Clean a policy document while keeping metadata separate from body text.

    Args:
        text: Raw policy document content.
        metadata: Optional metadata mapping to preserve alongside the cleaned body.

    Returns:
        A CleanedPolicyDocument containing the metadata and cleaned policy body.

    Raises:
        TypeError: If the text is not a string or metadata is not a mapping.
        ValueError: If the body text is empty after cleaning.
    """
    if not isinstance(text, str):
        raise TypeError("Policy content must be a string.")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise TypeError("Policy metadata must be a mapping or None.")

    extracted_metadata: dict[str, str]
    cleaned_body: str

    if metadata is not None:
        extracted_metadata = {str(key): str(value) for key, value in metadata.items()}
        cleaned_body = clean_policy_text(text)
    else:
        extracted_metadata, cleaned_body = extract_policy_metadata(text)

    if not cleaned_body.strip():
        raise ValueError("Policy document is empty after cleaning.")

    return CleanedPolicyDocument(metadata=extracted_metadata, text=cleaned_body)


__all__ = [
    "CleanedPolicyDocument",
    "clean_policy_document",
    "clean_policy_text",
    "extract_policy_metadata",
]
