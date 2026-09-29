"""Hybrid retrieval that combines local keyword and vector evidence.

Scoring approach:
- Each strategy produces its own candidate list and raw scores.
- Raw scores are normalized to the range [0, 1] using min-max normalization over
  the candidate set for that strategy.
- The normalized keyword and vector scores are then combined with configurable
  weights, using a weighted sum: final = w_k * keyword_norm + w_v * vector_norm.
- The final score is used for the combined ranking, with a stable chunk_id tie
  breaker to keep the ordering deterministic for the same corpus and query.

This stays fully local to the project and avoids any external paid search service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from rag.retrieval.keyword_retriever import KeywordRetriever
from rag.retrieval.retriever import VectorRetriever


class HybridRetrievalError(ValueError):
    """Raised when the hybrid retriever receives invalid configuration or input."""


@dataclass(frozen=True)
class HybridMatch:
    """A chunk produced by the hybrid ranker with a combined score."""

    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]


class HybridRetriever:
    """Fuse keyword and vector retrieval signals into a single ranked result set."""

    def __init__(
        self,
        keyword_retriever: KeywordRetriever,
        vector_retriever: VectorRetriever,
        *,
        keyword_weight: float = 0.5,
        vector_weight: float = 0.5,
        top_k: int = 5,
    ) -> None:
        if not isinstance(keyword_retriever, KeywordRetriever):
            raise HybridRetrievalError("keyword_retriever must be a KeywordRetriever")
        if not isinstance(vector_retriever, VectorRetriever):
            raise HybridRetrievalError("vector_retriever must be a VectorRetriever")
        if not isinstance(keyword_weight, (int, float)) or isinstance(keyword_weight, bool):
            raise HybridRetrievalError("keyword_weight must be a number")
        if not isinstance(vector_weight, (int, float)) or isinstance(vector_weight, bool):
            raise HybridRetrievalError("vector_weight must be a number")
        if keyword_weight < 0 or vector_weight < 0:
            raise HybridRetrievalError("weights must be non-negative")
        if keyword_weight + vector_weight <= 0:
            raise HybridRetrievalError("keyword_weight + vector_weight must be greater than zero")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise HybridRetrievalError("top_k must be a positive integer")

        self.keyword_retriever = keyword_retriever
        self.vector_retriever = vector_retriever
        self.keyword_weight = float(keyword_weight)
        self.vector_weight = float(vector_weight)
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: Mapping[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> list[HybridMatch]:
        """Return the combined ranking for the query, with optional metadata filters."""
        if not isinstance(query, str) or not query.strip():
            raise HybridRetrievalError("query must be a non-empty string")
        normalized_top_k = self._validate_top_k(self.top_k if top_k is None else top_k)
        normalized_filters = self._normalize_filters(filters, **filter_kwargs)

        keyword_candidates = self.keyword_retriever.retrieve(
            query,
            top_k=self._candidate_cap(self.keyword_retriever),
            filters=normalized_filters or None,
        )
        vector_candidates = self.vector_retriever.retrieve(
            query,
            top_k=self._candidate_cap(self.vector_retriever),
            filters=normalized_filters or None,
        )

        combined = self._combine_scores(keyword_candidates, vector_candidates)
        ranked = sorted(combined.values(), key=lambda item: (-item.score, item.chunk_id))
        return ranked[:normalized_top_k]

    def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: Mapping[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> list[HybridMatch]:
        """Alias for retrieve for the retriever API style used across the package."""
        return self.retrieve(query, top_k=top_k, filters=filters, **filter_kwargs)

    @staticmethod
    def _validate_top_k(top_k: int) -> int:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise HybridRetrievalError("top_k must be a positive integer")
        return top_k

    @staticmethod
    def _normalize_filters(
        filters: Mapping[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> dict[str, str]:
        merged: dict[str, Any] = {}
        if filters is not None:
            if not isinstance(filters, Mapping):
                raise HybridRetrievalError("filters must be a mapping of metadata fields to values")
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
                raise HybridRetrievalError("Filter field names must be non-empty strings")
            normalized_key = field_name.casefold()
            if normalized_key not in allowed_fields:
                invalid_fields.append(field_name)
                continue
            if raw_value is None:
                raise HybridRetrievalError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized_value = str(raw_value).strip()
            if not normalized_value:
                raise HybridRetrievalError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized[normalized_key] = normalized_value.casefold()

        if invalid_fields:
            invalid = ", ".join(sorted(set(invalid_fields)))
            raise HybridRetrievalError(
                "Unsupported filter fields: "
                f"{invalid}. Allowed fields are: category, policy_id, version, status, department"
            )
        return normalized

    @staticmethod
    def _candidate_cap(retriever: Any) -> int:
        if hasattr(retriever, "chunks"):
            chunks = getattr(retriever, "chunks")
            if isinstance(chunks, Iterable) and not isinstance(chunks, (str, bytes)):
                try:
                    return len(list(chunks))
                except TypeError:
                    pass
        if hasattr(retriever, "vector_store"):
            vector_store = getattr(retriever, "vector_store")
            if hasattr(vector_store, "__len__"):
                return len(vector_store)
        return 1

    @staticmethod
    def _normalize_match_scores(matches: Iterable[Any]) -> dict[str, float]:
        scored = list(matches)
        if not scored:
            return {}

        values = [float(item.score) for item in scored]
        minimum = min(values)
        maximum = max(values)
        if maximum == minimum:
            return {item.chunk_id: 1.0 for item in scored}
        return {
            item.chunk_id: (float(item.score) - minimum) / (maximum - minimum)
            for item in scored
        }

    def _combine_scores(
        self,
        keyword_matches: Iterable[Any],
        vector_matches: Iterable[Any],
    ) -> dict[str, HybridMatch]:
        keyword_scores = self._normalize_match_scores(keyword_matches)
        vector_scores = self._normalize_match_scores(vector_matches)
        combined: dict[str, HybridMatch] = {}

        all_candidate_ids = set(keyword_scores) | set(vector_scores)
        for chunk_id in sorted(all_candidate_ids):
            keyword_score = keyword_scores.get(chunk_id, 0.0)
            vector_score = vector_scores.get(chunk_id, 0.0)
            combined_score = (
                self.keyword_weight * keyword_score + self.vector_weight * vector_score
            )

            source_match = next(
                (match for match in keyword_matches if getattr(match, "chunk_id", None) == chunk_id),
                None,
            )
            if source_match is None:
                source_match = next(
                    (match for match in vector_matches if getattr(match, "chunk_id", None) == chunk_id),
                    None,
                )
            if source_match is None:
                continue

            combined[chunk_id] = HybridMatch(
                chunk_id=chunk_id,
                score=combined_score,
                text=getattr(source_match, "text", ""),
                metadata=dict(getattr(source_match, "metadata", {}) or {}),
            )

        return combined


__all__ = ["HybridMatch", "HybridRetrievalError", "HybridRetriever"]
