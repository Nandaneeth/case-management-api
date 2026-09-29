"""Strategy-agnostic reranking for retrieved policy candidates.

The reranker works on candidate objects produced by any retrieval strategy,
including vector, keyword, or hybrid retrieval. It does not depend on the source
retriever implementation and simply reorders the given candidates based on the
query-to-document relevance for the current request.

Scoring approach:
- tokenize the query and the candidate text
- remove very common stopwords
- compute lexical overlap and token-frequency signal
- add a small prior-score contribution when the candidate already has a score
- sort descending by the final relevance score and break ties by chunk_id for
  deterministic ordering

This is intentionally lightweight and local; it does not add external services or
LLM generation.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class RerankerError(ValueError):
    """Raised when a rerank operation receives invalid inputs."""


@dataclass(frozen=True)
class RerankedCandidate:
    """Candidate item after reranking, preserving the original metadata."""

    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]


class Reranker:
    """Reorder a list of retrieved candidates using local lexical relevance."""

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

    def rerank(
        self,
        query: str,
        candidates: Iterable[Any],
        top_k: int | None = None,
    ) -> list[Any]:
        """Return a reordered list of candidates ranked by query relevance."""
        if not isinstance(query, str) or not query.strip():
            raise RerankerError("query must be a non-empty string")
        if top_k is not None and (
            not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0
        ):
            raise RerankerError("top_k must be a positive integer")

        candidate_list = list(candidates)
        if not candidate_list:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        ranked = sorted(
            (
                self._score_candidate(query_tokens, candidate)
                for candidate in candidate_list
            ),
            key=lambda item: (-item[0], item[1]),
        )
        final_results = [candidate for _, _, candidate in ranked]
        if top_k is not None:
            return final_results[:top_k]
        return final_results

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        if not isinstance(text, str):
            return []
        tokens = re.findall(r"[a-z0-9]+(?:['-][a-z0-9]+)?", text.casefold())
        return [token for token in tokens if token not in cls._STOPWORDS and len(token) > 1]

    @classmethod
    def _candidate_text(cls, candidate: Any) -> str:
        if hasattr(candidate, "text"):
            value = getattr(candidate, "text")
            if isinstance(value, str):
                return value
        if isinstance(candidate, Mapping):
            value = candidate.get("text", "")
            if isinstance(value, str):
                return value
        return ""

    @classmethod
    def _candidate_metadata(cls, candidate: Any) -> dict[str, Any]:
        if hasattr(candidate, "metadata"):
            value = getattr(candidate, "metadata")
            if isinstance(value, Mapping):
                return dict(value)
        if isinstance(candidate, Mapping):
            value = candidate.get("metadata", {})
            if isinstance(value, Mapping):
                return dict(value)
        return {}

    @classmethod
    def _candidate_id(cls, candidate: Any) -> str:
        if hasattr(candidate, "chunk_id"):
            value = getattr(candidate, "chunk_id")
            if isinstance(value, str) and value.strip():
                return value
        if isinstance(candidate, Mapping):
            value = candidate.get("chunk_id")
            if isinstance(value, str) and value.strip():
                return value
        return ""

    @classmethod
    def _candidate_score(cls, candidate: Any) -> float:
        if hasattr(candidate, "score"):
            value = getattr(candidate, "score")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        if isinstance(candidate, Mapping):
            value = candidate.get("score")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        return 0.0

    @classmethod
    def _score_candidate(
        cls,
        query_tokens: list[str],
        candidate: Any,
    ) -> tuple[float, str, Any]:
        text = cls._candidate_text(candidate)
        if not text.strip():
            return (0.0, cls._candidate_id(candidate), candidate)

        doc_tokens = cls._tokenize(text)
        if not doc_tokens:
            return (0.0, cls._candidate_id(candidate), candidate)

        doc_counts = Counter(doc_tokens)
        query_set = set(query_tokens)
        matched_terms = query_set & set(doc_counts)
        overlap_ratio = (len(matched_terms) / len(query_set)) if query_set else 0.0
        term_frequency = (
            sum(doc_counts[token] for token in matched_terms) / len(doc_tokens)
            if doc_tokens
            else 0.0
        )
        prior_score = cls._normalize_score(cls._candidate_score(candidate))

        lexical_score = 0.55 * overlap_ratio + 0.45 * term_frequency
        score = 0.65 * lexical_score + 0.35 * prior_score
        return (score, cls._candidate_id(candidate), candidate)

    @staticmethod
    def _normalize_score(value: float) -> float:
        if not math.isfinite(value):
            return 0.0
        return max(0.0, min(1.0, value))


__all__ = ["RerankedCandidate", "Reranker", "RerankerError"]
