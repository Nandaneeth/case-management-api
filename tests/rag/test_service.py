"""Tests for refusal-safe RAG orchestration."""

from dataclasses import dataclass
from typing import Any, Mapping

from rag.generation.base import GenerationRequest, GenerationResult
from rag.service import RAGService


@dataclass(frozen=True)
class Candidate:
    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]


class StubRetriever:
    def __init__(self, candidates: list[Candidate]) -> None:
        self.candidates = candidates
        self.calls: list[tuple[str, Mapping[str, Any] | None]] = []

    def retrieve(self, question: str, top_k: int, filters: Mapping[str, Any] | None = None) -> list[Candidate]:
        self.calls.append((question, filters))
        return self.candidates[:top_k]


class StubReranker:
    def rerank(self, query: str, candidates: list[Candidate], top_k: int) -> list[Candidate]:
        return candidates[:top_k]


class MockGeneration:
    def __init__(self) -> None:
        self.calls: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls.append(request)
        return GenerationResult(
            text=f"Answer for {request.query} using {len(request.context)} context chunks.",
            provider="mock",
        )


def candidate(score: float, chunk_id: str = "chunk-1") -> Candidate:
    return Candidate(
        chunk_id=chunk_id,
        score=score,
        text="The policy requires identity verification.",
        metadata={"policy_id": "POL-001", "source": "identity-policy.md"},
    )


def make_service(candidates: list[Candidate], generator: MockGeneration) -> RAGService:
    return RAGService(
        StubRetriever(candidates),
        generator,
        reranker=StubReranker(),
        min_similarity_score=0.70,
    )


def test_fully_supported_question_generates_answer_and_sources() -> None:
    generator = MockGeneration()
    response = make_service([candidate(0.91)], generator).answer("What verification is required?")

    assert response.supported is True
    assert response.answer == "Answer for What verification is required? using 1 context chunks."
    assert response.sources == ["identity-policy.md (POL-001)"]
    assert len(generator.calls) == 1
    assert generator.calls[0].context == ("The policy requires identity verification.",)


def test_partially_supported_question_refuses_without_fabricating() -> None:
    generator = MockGeneration()
    response = make_service([candidate(0.69)], generator).answer("What verification and escalation are required?")

    assert response.supported is False
    assert "insufficient" in response.explanation.lower()
    assert response.answer == ""
    assert response.sources == []
    assert generator.calls == []


def test_completely_unsupported_question_refuses() -> None:
    generator = MockGeneration()
    response = make_service([candidate(0.10)], generator).answer("What is the office catering policy?")

    assert response.supported is False
    assert "insufficient" in response.explanation.lower()
    assert generator.calls == []


def test_no_retrieval_results_refuse() -> None:
    generator = MockGeneration()
    response = make_service([], generator).answer("What does the policy require?")

    assert response.supported is False
    assert "no policy context was retrieved" in response.explanation.lower()
    assert response.sources == []
    assert generator.calls == []


def test_below_threshold_scores_refuse_without_lowering_threshold() -> None:
    generator = MockGeneration()
    response = make_service([candidate(0.6999)], generator).answer("What is required?")

    assert response.supported is False
    assert "0.70" in response.explanation
    assert generator.calls == []