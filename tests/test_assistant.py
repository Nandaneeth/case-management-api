"""API tests for the policy assistant endpoint."""

from dataclasses import dataclass
from typing import Any, Mapping

import pytest
from fastapi.testclient import TestClient

from app.api.routes import assistant as assistant_routes
from app.main import app
from app.services.assistant_service import AssistantService
from rag.generation.mock import MockLLMProvider
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
        self.calls: list[tuple[str, int, Mapping[str, Any] | None]] = []

    def retrieve(
        self,
        question: str,
        top_k: int,
        filters: Mapping[str, Any] | None = None,
    ) -> list[Candidate]:
        self.calls.append((question, top_k, filters))
        return self.candidates[:top_k]


def policy_candidate(score: float = 0.95) -> Candidate:
    return Candidate(
        chunk_id="chunk-001",
        score=score,
        text="Password resets require identity verification.",
        metadata={
            "policy_id": "POL-001",
            "source": "identity-policy.md",
            "category": "access",
            "status": "active",
        },
    )


def install_service(
    client: TestClient,
    retriever: StubRetriever,
    response_template: str | None = None,
) -> None:
    rag_service = RAGService(
        retriever,
        MockLLMProvider(response_template=response_template),
        top_k=5,
        min_similarity_score=0.70,
    )
    assistant_service = AssistantService(rag_service=rag_service)
    app.dependency_overrides[assistant_routes.get_assistant_service] = (
        lambda: assistant_service
    )


def test_valid_query_without_filters_returns_expected_shape(client: TestClient) -> None:
    retriever = StubRetriever([policy_candidate()])
    install_service(client, retriever, "Grounded password reset answer")

    response = client.post("/assistant/query", json={"question": "How do I reset a password?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Grounded password reset answer",
        "supported": True,
        "sources": ["identity-policy.md (POL-001)"],
        "retrieval_metadata": {
            "top_k_used": 5,
            "filters": {},
            "chunk_count": 1,
            "supported": True,
        },
    }
    assert retriever.calls == [("How do I reset a password?", 5, None)]


@pytest.mark.parametrize(
    "payload",
    [
        {"question": ""},
        {"question": "x" * 2001},
        {"question": "valid question", "top_k": 0},
        {"question": "valid question", "top_k": 21},
    ],
)
def test_invalid_query_returns_422(client: TestClient, payload: dict[str, Any]) -> None:
    response = client.post("/assistant/query", json=payload)

    assert response.status_code == 422


def test_supported_question_uses_mock_provider(client: TestClient) -> None:
    retriever = StubRetriever([policy_candidate()])
    install_service(client, retriever, "Mock supported answer")

    response = client.post("/assistant/query", json={"question": "What is required?"})

    assert response.status_code == 200
    assert response.json()["supported"] is True
    assert response.json()["sources"] == ["identity-policy.md (POL-001)"]


def test_unsupported_question_has_no_fabricated_sources(client: TestClient) -> None:
    retriever = StubRetriever([])
    install_service(client, retriever, "This answer must never be returned")

    response = client.post("/assistant/query", json={"question": "What is unrelated?"})

    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is False
    assert body["answer"] == ""
    assert body["sources"] == []
    assert body["retrieval_metadata"]["chunk_count"] == 0


def test_metadata_filters_and_top_k_reach_retrieval(client: TestClient) -> None:
    retriever = StubRetriever([policy_candidate()])
    install_service(client, retriever, "Filtered answer")

    response = client.post(
        "/assistant/query",
        json={
            "question": "What is required?",
            "category": "access",
            "policy_id": "POL-001",
            "status": "active",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    assert retriever.calls == [
        (
            "What is required?",
            2,
            {"category": "access", "policy_id": "POL-001", "status": "active"},
        )
    ]
    assert response.json()["retrieval_metadata"]["top_k_used"] == 2
    assert response.json()["retrieval_metadata"]["filters"] == {
        "category": "access",
        "policy_id": "POL-001",
        "status": "active",
    }