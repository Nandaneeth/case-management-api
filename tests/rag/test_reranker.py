"""Tests for lightweight reranking of retrieved policy candidates."""

from dataclasses import dataclass
from typing import Any

import pytest

from rag.retrieval.reranker import Reranker, RerankerError


@dataclass
class Candidate:
    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]


@pytest.fixture
def candidates() -> list[Candidate]:
    return [
        Candidate(
            chunk_id="low-match",
            score=0.10,
            text="This section explains service outage procedures and customer support steps.",
            metadata={"policy_id": "POL-OPS-009", "category": "Operations"},
        ),
        Candidate(
            chunk_id="strong-match",
            score=0.90,
            text="This policy covers password reset verification, identity checks, and account recovery steps.",
            metadata={"policy_id": "POL-ACC-001", "category": "Authentication and Access"},
        ),
        Candidate(
            chunk_id="moderate-match",
            score=0.75,
            text="Guidance on customer account recovery and password reset experience.",
            metadata={"policy_id": "POL-ACC-002", "category": "Identity and Access Management"},
        ),
    ]


def test_reranker_orders_candidates_by_query_relevance(candidates: list[Candidate]) -> None:
    ranked = Reranker().rerank("How do I reset my password?", candidates)

    assert [item.chunk_id for item in ranked] == ["strong-match", "moderate-match", "low-match"]


def test_reranker_respects_top_k(candidates: list[Candidate]) -> None:
    ranked = Reranker().rerank("password reset", candidates, top_k=2)

    assert len(ranked) == 2
    assert [item.chunk_id for item in ranked][:2] == ["strong-match", "moderate-match"]


def test_reranker_returns_empty_for_empty_candidates() -> None:
    assert Reranker().rerank("password reset", []) == []


def test_reranker_preserves_metadata(candidates: list[Candidate]) -> None:
    ranked = Reranker().rerank("password reset", candidates)

    assert ranked[0].metadata["policy_id"] == "POL-ACC-001"
    assert ranked[0].metadata["category"] == "Authentication and Access"
    assert ranked[1].metadata["policy_id"] == "POL-ACC-002"


def test_reranker_rejects_invalid_query() -> None:
    with pytest.raises(RerankerError, match="non-empty"):
        Reranker().rerank("   ", [])
