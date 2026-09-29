"""Tests for production assistant policy-index construction and injection."""

import asyncio
from typing import Sequence

from app import dependencies
from app import main as app_main
from app.services.assistant_service import EmptyRetriever
from rag.embeddings.embedding_service import EmbeddingService


class LocalPolicyEmbeddingModel:
    """Small test double supplied through the existing EmbeddingService."""

    _topics = ("password", "payment", "refund", "outage")

    def get_sentence_embedding_dimension(self) -> int:
        return len(self._topics)

    def encode(
        self,
        texts: Sequence[str],
        *,
        normalize_embeddings: bool,
        batch_size: int,
    ) -> list[list[float]]:
        vectors = []
        for text in texts:
            lowered = text.casefold()
            vector = [float(lowered.count(topic)) for topic in self._topics]
            if not any(vector):
                vector = [0.01] * len(self._topics)
            if normalize_embeddings:
                norm = sum(value * value for value in vector) ** 0.5
                vector = [value / norm for value in vector]
            vectors.append(vector)
        return vectors


def test_policy_retriever_builder_indexes_local_policy_chunks(monkeypatch) -> None:
    monkeypatch.setattr(
        dependencies,
        "EmbeddingService",
        lambda: EmbeddingService(model=LocalPolicyEmbeddingModel()),
    )

    retriever = dependencies.build_policy_retriever()
    results = retriever.retrieve(
        "What should support do when a customer's payment fails?",
        top_k=5,
    )

    assert len(retriever.vector_store) > 0
    assert results
    assert any(result.metadata["policy_id"] == "POL-BILL-014" for result in results)


def test_application_lifespan_injects_built_retriever(monkeypatch) -> None:
    retriever = EmptyRetriever()
    monkeypatch.setattr(app_main, "build_policy_retriever", lambda: retriever)
    monkeypatch.setattr(app_main, "initialize_database", lambda: None)

    async def run_lifespan() -> None:
        async with app_main.lifespan(app_main.app):
            service = app_main.app.state.assistant_service
            assert service.rag_service.vector_retriever is retriever

    asyncio.run(run_lifespan())