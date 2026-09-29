"""Tests for hybrid keyword-plus-vector retrieval."""

from hashlib import sha256
from pathlib import Path
from typing import Sequence

import pytest

from rag.chunking.fixed_chunker import ChunkerConfig, chunk_policy_document
from rag.embeddings.embedding_service import EmbeddingService
from rag.ingestion.document_loader import load_policy_documents
from rag.retrieval.hybrid_retriever import HybridRetrievalError, HybridRetriever
from rag.retrieval.keyword_retriever import KeywordRetriever
from rag.retrieval.retriever import VectorRetriever


class PolicyKeywordModel:
    """Small deterministic model double with policy-topic dimensions."""

    _keywords = ("password", "payment", "refund", "outage")

    def get_sentence_embedding_dimension(self) -> int:
        return len(self._keywords)

    def encode(self, texts: Sequence[str], **_: object) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    @classmethod
    def _vector(cls, text: str) -> list[float]:
        lowered = text.lower()
        vector = [float(lowered.count(keyword)) for keyword in cls._keywords]
        if any(vector):
            return vector
        digest = sha256(text.encode("utf-8")).digest()
        return [float(byte + 1) for byte in digest[: len(cls._keywords)]]


@pytest.fixture
def policy_chunks() -> list[object]:
    policy_root = Path(__file__).parents[2] / "data" / "policies"
    documents = load_policy_documents(policy_root)
    chunks: list[object] = []
    for document in documents:
        chunks.extend(
            chunk_policy_document(
                text=document.text,
                policy_id=document.metadata.policy_id,
                source=document.metadata.source,
                metadata=document.metadata.to_dict(),
                config=ChunkerConfig(chunk_size=600, overlap=0),
            )
        )
    return chunks


@pytest.fixture
def hybrid_retriever(policy_chunks: list[object]) -> HybridRetriever:
    keyword_retriever = KeywordRetriever(policy_chunks, top_k=5)
    vector_retriever = VectorRetriever(EmbeddingService(model=PolicyKeywordModel()), top_k=5)
    vector_retriever.index_chunks(policy_chunks)
    return HybridRetriever(
        keyword_retriever=keyword_retriever,
        vector_retriever=vector_retriever,
        keyword_weight=0.6,
        vector_weight=0.4,
        top_k=3,
    )


def test_hybrid_retrieval_is_deterministic_for_test_corpus(
    hybrid_retriever: HybridRetriever,
) -> None:
    first = hybrid_retriever.retrieve("How do I reset my password?")
    second = hybrid_retriever.retrieve("How do I reset my password?")

    assert first == second
    assert first
    assert first[0].metadata["policy_id"] == "POL-ACC-001"
    assert all(result.score >= 0.0 for result in first)


def test_hybrid_retrieval_supports_metadata_filters(
    hybrid_retriever: HybridRetriever,
) -> None:
    results = hybrid_retriever.retrieve(
        "How do I reset my password?",
        filters={"category": "Authentication and Access", "status": "Approved"},
    )

    assert results
    assert all(
        result.metadata.get("category", "").casefold() == "authentication and access"
        for result in results
    )
    assert all(result.metadata.get("status", "").casefold() == "approved" for result in results)


def test_hybrid_retriever_rejects_invalid_weight_configuration() -> None:
    keyword_retriever = KeywordRetriever([], top_k=3)
    vector_retriever = VectorRetriever(EmbeddingService(model=PolicyKeywordModel()), top_k=3)

    with pytest.raises(HybridRetrievalError, match="weights"):
        HybridRetriever(
            keyword_retriever=keyword_retriever,
            vector_retriever=vector_retriever,
            keyword_weight=-1,
            vector_weight=0.5,
        )
