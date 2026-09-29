"""Structure-aware recursive chunking for policy documents.

This chunker prefers meaningful policy boundaries such as headings, paragraphs,
procedure sections, exceptions, and escalation sections before falling back to a
fixed-size split. It keeps metadata and section context attached to each chunk and
assigns deterministic, unique IDs to each output chunk.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

from rag.chunking.fixed_chunker import Chunk, ChunkerConfig, ChunkingConfigError

DEFAULT_MAX_CHUNK_SIZE = 800
DEFAULT_OVERLAP = 80

_SECTION_KEYWORDS = (
    "purpose",
    "scope",
    "procedure",
    "exceptions",
    "escalation",
    "policy",
)


@dataclass(frozen=True)
class RecursiveChunkerConfig:
    """Configuration for recursive, structure-aware policy chunking."""

    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE
    overlap: int = DEFAULT_OVERLAP

    def __post_init__(self) -> None:
        """Validate the recursive chunker configuration."""
        if self.max_chunk_size <= 0:
            raise ChunkingConfigError("max_chunk_size must be greater than 0")
        if self.overlap < 0:
            raise ChunkingConfigError("overlap must be greater than or equal to 0")
        if self.overlap >= self.max_chunk_size:
            raise ChunkingConfigError("overlap must be smaller than max_chunk_size")


@dataclass(frozen=True)
class RecursiveChunk:
    """Chunk output that preserves section-level context."""

    chunk_id: str
    policy_id: str
    source: str
    section: str
    metadata: dict[str, Any] = field(default_factory=dict)
    text: str = ""
    start_index: int = 0
    end_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary-friendly representation of the chunk."""
        return {
            "chunk_id": self.chunk_id,
            "policy_id": self.policy_id,
            "source": self.source,
            "section": self.section,
            "metadata": self.metadata,
            "text": self.text,
            "start_index": self.start_index,
            "end_index": self.end_index,
        }


def chunk_policy_document(
    text: str,
    policy_id: str,
    source: str,
    metadata: Mapping[str, Any] | None = None,
    config: RecursiveChunkerConfig | None = None,
) -> list[RecursiveChunk]:
    """Chunk a policy document by structure before falling back to a fixed-size split.

    The recursive strategy first prefers clean section boundaries and paragraph
    groupings so policy content remains meaningful to downstream retrieval. If the
    input remains too large, it falls back to a deterministic fixed-size split with
    overlap.

    Args:
        text: Cleaned policy text to chunk.
        policy_id: Policy identifier to attach to every chunk.
        source: Source file or document label.
        metadata: Optional metadata to carry through each generated chunk.
        config: Configuration for maximum chunk size and overlap.

    Returns:
        Deterministic structure-aware chunks with policy metadata preserved.

    Raises:
        TypeError: If inputs are of the wrong type.
        ValueError: If the text is empty or cannot be chunked.
        ChunkingConfigError: If the chunking configuration is invalid.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text.strip():
        raise ValueError("Policy text cannot be empty")
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise TypeError("policy_id must be a non-empty string")
    if not isinstance(source, str) or not source.strip():
        raise TypeError("source must be a non-empty string")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping or None")

    active_config = config or RecursiveChunkerConfig()
    if not isinstance(active_config, RecursiveChunkerConfig):
        raise TypeError("config must be a RecursiveChunkerConfig instance or None")

    normalized_metadata = dict(metadata or {})
    sections = _split_into_sections(text)
    chunks: list[RecursiveChunk] = []

    for section_name, section_text in sections:
        if len(section_text) <= active_config.max_chunk_size:
            chunks.extend(
                _build_chunk_group(
                    section_text,
                    policy_id=policy_id,
                    source=source,
                    section=section_name,
                    metadata=normalized_metadata,
                    max_chunk_size=active_config.max_chunk_size,
                    overlap=active_config.overlap,
                )
            )
            continue

        chunks.extend(
            _build_chunk_group(
                section_text,
                policy_id=policy_id,
                source=source,
                section=section_name,
                metadata=normalized_metadata,
                max_chunk_size=active_config.max_chunk_size,
                overlap=active_config.overlap,
            )
        )

    if not chunks:
        raise ValueError("No chunks were generated from the provided text")
    return chunks


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split policy text into section blocks using headings and content patterns."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks: list[tuple[str, str]] = []
    current_heading = "overview"
    current_lines: list[str] = []

    for line in normalized.split("\n"):
        heading_match = re.match(r"^(?:#+\s*)?(?P<title>Purpose|Scope|Procedure|Exceptions|Escalation guidance|Escalation|Policy|Overview)\s*$", line, flags=re.IGNORECASE)
        if heading_match:
            if current_lines:
                blocks.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = heading_match.group("title").strip().lower()
            current_lines = []
            continue

        if line.strip():
            current_lines.append(line.strip())

    if current_lines:
        blocks.append((current_heading, "\n".join(current_lines).strip()))

    if not blocks:
        blocks.append(("overview", normalized.strip()))

    return blocks


def _build_chunk_group(
    text: str,
    policy_id: str,
    source: str,
    section: str,
    metadata: Mapping[str, Any],
    max_chunk_size: int,
    overlap: int,
) -> list[RecursiveChunk]:
    """Create deterministic chunks for a section using a fixed-size fallback."""
    if len(text) <= max_chunk_size:
        return [
            _make_chunk(
                text=text,
                policy_id=policy_id,
                source=source,
                section=section,
                metadata=metadata,
                start_index=0,
                end_index=len(text),
                chunk_index=0,
            )
        ]

    chunks: list[RecursiveChunk] = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(start + max_chunk_size, len(text))
        chunk_text = text[start:end]
        if not chunk_text:
            break

        chunks.append(
            _make_chunk(
                text=chunk_text,
                policy_id=policy_id,
                source=source,
                section=section,
                metadata=metadata,
                start_index=start,
                end_index=end,
                chunk_index=chunk_index,
            )
        )

        if end == len(text):
            break

        start += max_chunk_size - overlap
        chunk_index += 1

    return chunks


def _make_chunk(
    text: str,
    policy_id: str,
    source: str,
    section: str,
    metadata: Mapping[str, Any],
    start_index: int,
    end_index: int,
    chunk_index: int,
) -> RecursiveChunk:
    """Create a single recursive chunk with deterministic IDs and metadata."""
    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{policy_id}:{source}:{section}:{start_index}:{end_index}:{chunk_index}"))
    return RecursiveChunk(
        chunk_id=chunk_id,
        policy_id=policy_id,
        source=source,
        section=section,
        metadata={**dict(metadata), "chunk_index": chunk_index},
        text=text,
        start_index=start_index,
        end_index=end_index,
    )


__all__ = [
    "RecursiveChunk",
    "RecursiveChunkerConfig",
    "ChunkingConfigError",
    "chunk_policy_document",
    "DEFAULT_MAX_CHUNK_SIZE",
    "DEFAULT_OVERLAP",
]
