"""Small local vector-store abstraction for policy chunk embeddings."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


class VectorStoreError(ValueError):
    """Raised when a vector-store operation receives invalid data."""


@dataclass(frozen=True)
class VectorMatch:
    """A stored chunk and its similarity to a query vector."""

    chunk_id: str
    score: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class _StoredChunk:
    """Internal representation of one indexed chunk."""

    chunk_id: str
    embedding: tuple[float, ...]
    metadata: dict[str, Any]


class VectorStore:
    """Store chunk embeddings and perform in-memory cosine similarity search."""

    def __init__(self, default_top_k: int = 5) -> None:
        if not isinstance(default_top_k, int) or isinstance(default_top_k, bool):
            raise VectorStoreError("default_top_k must be a positive integer")
        if default_top_k <= 0:
            raise VectorStoreError("default_top_k must be a positive integer")

        self._default_top_k = default_top_k
        self._dimension: int | None = None
        self._chunks: dict[str, _StoredChunk] = {}

    @property
    def dimension(self) -> int | None:
        """Return the indexed vector dimension, or ``None`` for an empty store."""
        return self._dimension

    def __len__(self) -> int:
        """Return the number of indexed chunks."""
        return len(self._chunks)

    def add_chunk(
        self,
        chunk_id: str,
        embedding: Sequence[float],
        metadata: Mapping[str, Any],
    ) -> None:
        """Insert or replace a chunk embedding and its policy metadata."""
        normalized_id = self._validate_chunk_id(chunk_id)
        normalized_embedding = self._validate_embedding(embedding)
        if not isinstance(metadata, Mapping):
            raise VectorStoreError("metadata must be a mapping")

        if self._dimension is None:
            self._dimension = len(normalized_embedding)
        elif len(normalized_embedding) != self._dimension:
            raise VectorStoreError(
                f"Embedding dimension {len(normalized_embedding)} does not match "
                f"the store dimension {self._dimension}"
            )

        self._chunks[normalized_id] = _StoredChunk(
            chunk_id=normalized_id,
            embedding=normalized_embedding,
            metadata=dict(metadata),
        )

    def search(
        self,
        query_embedding: Sequence[float],
        top_k: int | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> list[VectorMatch]:
        """Return the highest-scoring stored chunks for a query embedding."""
        requested_top_k = self._validate_top_k(
            self._default_top_k if top_k is None else top_k
        )
        if not self._chunks:
            return []

        query = self._validate_embedding(query_embedding)
        if len(query) != self._dimension:
            raise VectorStoreError(
                f"Query dimension {len(query)} does not match the store dimension "
                f"{self._dimension}"
            )

        normalized_filters = self._normalize_filters(filters)
        ranked = sorted(
            (
                VectorMatch(
                    chunk_id=chunk.chunk_id,
                    score=self._cosine_similarity(query, chunk.embedding),
                    metadata=dict(chunk.metadata),
                )
                for chunk in self._chunks.values()
            ),
            key=lambda match: (-match.score, match.chunk_id),
        )

        if normalized_filters:
            ranked = [
                match
                for match in ranked
                if all(
                    self._metadata_matches(match.metadata.get(field), value)
                    for field, value in normalized_filters.items()
                )
            ]

        return ranked[:requested_top_k]

    def save(self, path: str | Path) -> None:
        """Persist the local index as a JSON file."""
        destination = Path(path)
        payload = {
            "default_top_k": self._default_top_k,
            "dimension": self._dimension,
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "embedding": list(chunk.embedding),
                    "metadata": chunk.metadata,
                }
                for chunk in self._chunks.values()
            ],
        }
        try:
            destination.write_text(json.dumps(payload), encoding="utf-8")
        except (OSError, TypeError, ValueError) as exc:
            raise VectorStoreError(f"Unable to save vector index to '{destination}'") from exc

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        """Load a JSON index previously written by :meth:`save`."""
        source = Path(path)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
            store = cls(default_top_k=payload["default_top_k"])
            for chunk in payload["chunks"]:
                store.add_chunk(chunk["chunk_id"], chunk["embedding"], chunk["metadata"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise VectorStoreError(f"Unable to load vector index from '{source}'") from exc

        if payload.get("dimension") != store.dimension:
            if payload.get("dimension") is not None or store.dimension is not None:
                raise VectorStoreError("Persisted vector dimension is inconsistent")
        return store

    @staticmethod
    def _normalize_filters(filters: Mapping[str, Any] | None) -> dict[str, str]:
        if filters is None:
            return {}
        if not isinstance(filters, Mapping):
            raise VectorStoreError("filters must be a mapping of metadata fields to values")

        allowed_fields = {"category", "policy_id", "version", "status", "department"}
        normalized: dict[str, str] = {}
        for raw_key, raw_value in filters.items():
            key = str(raw_key).strip()
            if not key:
                raise VectorStoreError("Filter field names must be non-empty strings")
            field_name = key.casefold()
            if field_name not in allowed_fields:
                invalid = ", ".join(sorted({field_name for field_name in filters.keys()}))
                raise VectorStoreError(
                    "Unsupported filter fields: "
                    f"{invalid}. Allowed fields are: category, policy_id, version, status, department"
                )
            if raw_value is None:
                raise VectorStoreError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized_value = str(raw_value).strip()
            if not normalized_value:
                raise VectorStoreError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized[field_name] = normalized_value.casefold()
        return normalized

    @staticmethod
    def _metadata_matches(metadata_value: Any, expected_value: str) -> bool:
        if metadata_value is None:
            return False
        return str(metadata_value).strip().casefold() == expected_value

    @staticmethod
    def _validate_chunk_id(chunk_id: str) -> str:
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise VectorStoreError("chunk_id must be a non-empty string")
        return chunk_id

    @staticmethod
    def _validate_embedding(embedding: Sequence[float]) -> tuple[float, ...]:
        if isinstance(embedding, (str, bytes)) or not isinstance(embedding, Sequence):
            raise VectorStoreError("embedding must be a non-empty sequence of numbers")
        if not embedding:
            raise VectorStoreError("embedding must be a non-empty sequence of numbers")
        try:
            values = tuple(float(value) for value in embedding)
        except (TypeError, ValueError) as exc:
            raise VectorStoreError("embedding must contain only numbers") from exc
        if any(not math.isfinite(value) for value in values):
            raise VectorStoreError("embedding values must be finite")
        if not any(value != 0.0 for value in values):
            raise VectorStoreError("embedding must not be a zero vector")
        return values

    @staticmethod
    def _validate_top_k(top_k: int) -> int:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise VectorStoreError("top_k must be a positive integer")
        return top_k

    @staticmethod
    def _cosine_similarity(
        left: Sequence[float], right: Sequence[float]
    ) -> float:
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


__all__ = ["VectorMatch", "VectorStore", "VectorStoreError"]