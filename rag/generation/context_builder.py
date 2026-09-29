"""Build a controlled context string from retrieved policy chunks.

This component is intentionally narrow: it only accepts retrieval candidates that
look like policy chunks, removes duplicates, caps the number of chunks, and
formats a small, source-aware context block that can safely be passed to a
generator. It does not perform generation or any external retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class ContextBuilderError(ValueError):
    """Raised when a chunk cannot be transformed into a valid generator context."""


@dataclass(frozen=True)
class ContextChunk:
    """Normalized chunk representation used for context assembly."""

    chunk_id: str
    policy_id: str
    source: str
    text: str
    metadata: dict[str, Any]


class ContextBuilder:
    """Build a controlled context string from retrieved policy chunks."""

    def __init__(self, max_chunks: int = 5) -> None:
        if not isinstance(max_chunks, int) or isinstance(max_chunks, bool) or max_chunks <= 0:
            raise ContextBuilderError("max_chunks must be a positive integer")
        self.max_chunks = max_chunks

    def build(self, chunks: Iterable[Any], max_chunks: int | None = None) -> str:
        """Convert retrieved chunks into a small, ordered context string."""
        candidate_chunks = list(chunks or [])
        if not candidate_chunks:
            return ""

        effective_limit = self.max_chunks if max_chunks is None else max_chunks
        if not isinstance(effective_limit, int) or isinstance(effective_limit, bool) or effective_limit <= 0:
            raise ContextBuilderError("max_chunks must be a positive integer")

        normalized = [self._normalize_chunk(chunk) for chunk in candidate_chunks]
        seen: set[str] = set()
        unique_chunks: list[ContextChunk] = []
        for chunk in normalized:
            if chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk_id)
            unique_chunks.append(chunk)

        selected = unique_chunks[:effective_limit]
        if not selected:
            return ""

        context_blocks: list[str] = []
        for index, chunk in enumerate(selected, start=1):
            metadata_lines = [
                f"Policy ID: {chunk.policy_id}",
                f"Chunk ID: {chunk.chunk_id}",
                f"Source: {chunk.source}",
            ]
            for key, value in chunk.metadata.items():
                if key in {"policy_id", "chunk_id", "source", "text"}:
                    continue
                metadata_lines.append(f"{self._format_label(key)}: {value}")
            metadata_lines = sorted(set(metadata_lines), key=lambda line: line.lower())
            context_blocks.append(
                "\n".join(
                    [
                        f"Context chunk {index}:",
                        *metadata_lines,
                        "Text:",
                        self._clean_text(chunk.text),
                    ]
                )
            )
        return "\n\n".join(context_blocks)

    @staticmethod
    def _format_label(key: str) -> str:
        if not isinstance(key, str):
            return "Metadata"
        return key.replace("_", " ").title()

    @staticmethod
    def _clean_text(text: str) -> str:
        if not isinstance(text, str):
            return ""
        cleaned = text.strip().replace("\r\n", "\n").replace("\r", "\n")
        return cleaned

    @classmethod
    def _normalize_chunk(cls, chunk: Any) -> ContextChunk:
        if hasattr(chunk, "chunk_id") and hasattr(chunk, "text"):
            metadata = getattr(chunk, "metadata", {})
            if metadata is None:
                metadata = {}
            if not isinstance(metadata, Mapping):
                raise ContextBuilderError("Chunk metadata must be a mapping")
            chunk_id = getattr(chunk, "chunk_id")
            policy_id = metadata.get("policy_id")
            source = metadata.get("source")
            if not isinstance(chunk_id, str) or not chunk_id.strip():
                raise ContextBuilderError("Each chunk must include a non-empty chunk_id")
            if not isinstance(policy_id, str) or not policy_id.strip():
                raise ContextBuilderError("Each chunk must include a policy_id in metadata")
            if not isinstance(source, str) or not source.strip():
                raise ContextBuilderError("Each chunk must include a source in metadata")
            text = getattr(chunk, "text")
            if not isinstance(text, str):
                raise ContextBuilderError("Each chunk must include a text string")
            result_metadata = dict(metadata)
            result_metadata.setdefault("policy_id", policy_id)
            result_metadata.setdefault("source", source)
            return ContextChunk(
                chunk_id=chunk_id,
                policy_id=policy_id,
                source=source,
                text=text,
                metadata=result_metadata,
            )

        if isinstance(chunk, Mapping):
            metadata = chunk.get("metadata", {})
            if metadata is None:
                metadata = {}
            if not isinstance(metadata, Mapping):
                raise ContextBuilderError("Chunk metadata must be a mapping")
            chunk_id = chunk.get("chunk_id")
            policy_id = metadata.get("policy_id") or chunk.get("policy_id")
            source = metadata.get("source") or chunk.get("source")
            text = chunk.get("text", "")
            if not isinstance(chunk_id, str) or not chunk_id.strip():
                raise ContextBuilderError("Each chunk must include a non-empty chunk_id")
            if not isinstance(policy_id, str) or not policy_id.strip():
                raise ContextBuilderError("Each chunk must include a policy_id in metadata")
            if not isinstance(source, str) or not source.strip():
                raise ContextBuilderError("Each chunk must include a source in metadata")
            if not isinstance(text, str):
                raise ContextBuilderError("Each chunk must include a text string")
            result_metadata = dict(metadata)
            result_metadata.setdefault("policy_id", policy_id)
            result_metadata.setdefault("source", source)
            return ContextChunk(
                chunk_id=chunk_id,
                policy_id=policy_id,
                source=source,
                text=text,
                metadata=result_metadata,
            )

        raise ContextBuilderError("Chunk must expose chunk_id, text, and metadata")


__all__ = ["ContextBuilder", "ContextBuilderError", "ContextChunk"]
