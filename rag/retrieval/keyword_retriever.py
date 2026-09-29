"""Lightweight local keyword retrieval for policy chunks.

This strategy keeps the retrieval pipeline simple and fully local. It tokenizes
queries, indexes the available chunks, and ranks each chunk by keyword overlap and
term frequency so downstream code can use it without an external search service.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class KeywordRetrievalError(ValueError):
    """Raised when keyword retrieval receives invalid input."""


@dataclass(frozen=True)
class KeywordMatch:
    """A chunk and its keyword relevance score."""

    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]


class KeywordRetriever:
    """Score chunks using a lightweight local term-frequency approach."""

    _STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "do",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "why",
        "with",
        "you",
        "your",
    }

    def __init__(self, chunks: Iterable[Any] | None = None, top_k: int = 5) -> None:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise KeywordRetrievalError("top_k must be a positive integer")
        self.chunks = list(chunks) if chunks is not None else []
        self.top_k = top_k

    def index_chunks(self, chunks: Iterable[Any]) -> int:
        """Replace the indexed chunk set and return the count of indexed chunks."""
        self.chunks = list(chunks)
        return len(self.chunks)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: Mapping[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> list[KeywordMatch]:
        """Return the most relevant chunks for the query, ranked by keyword score."""
        if not isinstance(query, str) or not query.strip():
            raise KeywordRetrievalError("query must be a non-empty string")

        normalized_top_k = self._validate_top_k(self.top_k if top_k is None else top_k)
        normalized_filters = self._normalize_filters(filters, **filter_kwargs)
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.chunks:
            return []

        scores = self._score_query(query_tokens, self.chunks)
        if normalized_filters:
            scores = [
                match
                for match in scores
                if all(
                    self._metadata_matches(match.metadata.get(field), value)
                    for field, value in normalized_filters.items()
                )
            ]
        ranked = sorted(scores, key=lambda item: (-item.score, item.chunk_id))
        return ranked[:normalized_top_k]

    def search(self, query: str, top_k: int | None = None) -> list[KeywordMatch]:
        """Alias for retrieve to keep the public API consistent with other retrievers."""
        return self.retrieve(query, top_k=top_k)

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        if not isinstance(text, str):
            return []
        tokens = re.findall(r"[a-z0-9]+(?:['-][a-z0-9]+)?", text.casefold())
        return [token for token in tokens if token not in cls._STOPWORDS and len(token) > 1]

    @staticmethod
    def _normalize_filters(
        filters: Mapping[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> dict[str, str]:
        merged: dict[str, Any] = {}
        if filters is not None:
            if not isinstance(filters, Mapping):
                raise KeywordRetrievalError("filters must be a mapping of metadata fields to values")
            merged.update(dict(filters))
        merged.update(filter_kwargs)

        if not merged:
            return {}

        allowed_fields = {"category", "policy_id", "version", "status", "department"}
        normalized: dict[str, str] = {}
        invalid_fields: list[str] = []

        for raw_key, raw_value in merged.items():
            field_name = str(raw_key).strip()
            if not field_name:
                raise KeywordRetrievalError("Filter field names must be non-empty strings")
            normalized_key = field_name.casefold()
            if normalized_key not in allowed_fields:
                invalid_fields.append(field_name)
                continue
            if raw_value is None:
                raise KeywordRetrievalError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized_value = str(raw_value).strip()
            if not normalized_value:
                raise KeywordRetrievalError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized[normalized_key] = normalized_value.casefold()

        if invalid_fields:
            invalid = ", ".join(sorted(set(invalid_fields)))
            raise KeywordRetrievalError(
                "Unsupported filter fields: "
                f"{invalid}. Allowed fields are: category, policy_id, version, status, department"
            )
        return normalized

    @staticmethod
    def _metadata_matches(metadata_value: Any, expected_value: str) -> bool:
        if metadata_value is None:
            return False
        return str(metadata_value).strip().casefold() == expected_value

    @staticmethod
    def _validate_top_k(top_k: int) -> int:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise KeywordRetrievalError("top_k must be a positive integer")
        return top_k

    @staticmethod
    def _chunk_text(chunk: Any) -> str:
        text = getattr(chunk, "text", None)
        if text is None:
            raise KeywordRetrievalError("Each chunk must expose a text value")
        if not isinstance(text, str):
            raise KeywordRetrievalError("Chunk text must be a string")
        return text

    @staticmethod
    def _chunk_id(chunk: Any) -> str:
        chunk_id = getattr(chunk, "chunk_id", None)
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise KeywordRetrievalError("Each chunk must have a non-empty chunk_id")
        return chunk_id

    @staticmethod
    def _chunk_metadata(chunk: Any) -> dict[str, Any]:
        metadata = getattr(chunk, "metadata", {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, Mapping):
            raise KeywordRetrievalError("Chunk metadata must be a mapping")
        result = dict(metadata)
        if isinstance(chunk, Mapping):
            result = dict(chunk)
        return result

    @classmethod
    def _score_query(cls, query_tokens: list[str], chunks: list[Any]) -> list[KeywordMatch]:
        if not query_tokens:
            return []

        document_frequency = Counter()
        for chunk in chunks:
            chunk_tokens = cls._tokenize(cls._chunk_text(chunk))
            if chunk_tokens:
                document_frequency.update(set(chunk_tokens))

        total_documents = len(chunks) or 1
        scored: list[KeywordMatch] = []

        for chunk in chunks:
            chunk_tokens = cls._tokenize(cls._chunk_text(chunk))
            if not chunk_tokens:
                continue

            token_counts = Counter(chunk_tokens)
            score = 0.0
            query_terms = set(query_tokens)
            overlap = set(query_terms) & set(chunk_tokens)

            for token in query_terms:
                if token not in token_counts:
                    continue
                tf = token_counts[token] / len(chunk_tokens)
                idf = math.log((total_documents + 1.0) / (document_frequency.get(token, 0) + 1.0)) + 1.0
                score += tf * idf

            if overlap:
                score += (len(overlap) / len(query_terms)) * 0.75

            if score > 0:
                scored.append(
                    KeywordMatch(
                        chunk_id=cls._chunk_id(chunk),
                        score=score,
                        text=cls._chunk_text(chunk),
                        metadata=cls._chunk_metadata(chunk),
                    )
                )

        return scored


__all__ = ["KeywordMatch", "KeywordRetrievalError", "KeywordRetriever"]
