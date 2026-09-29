"""Fixed-size chunking for policy documents.

This module splits a cleaned policy document into deterministic, fixed-size text
chunks without performing embeddings or retrieval logic. It preserves document
metadata and assigns stable identifiers to each chunk for downstream processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
import uuid


DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 50


class ChunkingConfigError(ValueError):
    """Raised when the chunker is configured with invalid values."""


@dataclass(frozen=True)
class Chunk:
    """Single chunk produced from a policy document."""

    chunk_id: str
    policy_id: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    text: str = ""
    start_index: int = 0
    end_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary-friendly view of the chunk."""
        return {
            "chunk_id": self.chunk_id,
            "policy_id": self.policy_id,
            "source": self.source,
            "metadata": self.metadata,
            "text": self.text,
            "start_index": self.start_index,
            "end_index": self.end_index,
        }


@dataclass(frozen=True)
class ChunkerConfig:
    """Configuration for deterministic fixed-size chunking."""

    chunk_size: int = DEFAULT_CHUNK_SIZE
    overlap: int = DEFAULT_OVERLAP

    def __post_init__(self) -> None:
        """Validate the chunking configuration."""
        if self.chunk_size <= 0:
            raise ChunkingConfigError("chunk_size must be greater than 0")
        if self.overlap < 0:
            raise ChunkingConfigError("overlap must be greater than or equal to 0")
        if self.overlap >= self.chunk_size:
            raise ChunkingConfigError("overlap must be smaller than chunk_size")


def chunk_policy_document(
    text: str,
    policy_id: str,
    source: str,
    metadata: Mapping[str, Any] | None = None,
    config: ChunkerConfig | None = None,
) -> list[Chunk]:
    """Split a policy document into fixed-size overlapping chunks.

    Args:
        text: Cleaned policy text to chunk.
        policy_id: Identifier for the policy.
        source: Source label or file path associated with the policy.
        metadata: Optional extra metadata to preserve with each chunk.
        config: Optional chunker configuration. Defaults to a 500/50 split.

    Returns:
        A list of deterministic chunk objects with metadata and chunk IDs.

    Raises:
        TypeError: If the input values are not of the expected types.
        ValueError: If the document text is empty.
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

    active_config = config or ChunkerConfig()
    if not isinstance(active_config, ChunkerConfig):
        raise TypeError("config must be a ChunkerConfig instance or None")

    chunk_size = active_config.chunk_size
    overlap = active_config.overlap
    step = chunk_size - overlap

    normalized_metadata = dict(metadata or {})
    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]

        if not chunk_text:
            break

        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{policy_id}:{source}:{start}:{end}"))
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                policy_id=policy_id,
                source=source,
                metadata={**normalized_metadata, "chunk_index": index, "chunk_size": chunk_size},
                text=chunk_text,
                start_index=start,
                end_index=end,
            )
        )

        if end == len(text):
            break
        start += step
        index += 1

    if not chunks:
        raise ValueError("No chunks were generated from the provided text")

    return chunks


__all__ = [
    "Chunk",
    "ChunkerConfig",
    "ChunkingConfigError",
    "chunk_policy_document",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_OVERLAP",
]
