"""Tests for embedding-backed retrieval against the local policy corpus."""

from hashlib import sha256
from pathlib import Path
from typing import Sequence

import pytest

from rag.chunking.fixed_chunker import ChunkerConfig, chunk_policy_document
from rag.embeddings.embedding_service import EmbeddingService
from rag.ingestion.document_loader import load_policy_documents
from rag.retrieval.retriever import RetrieverError, VectorRetriever


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
def retriever() -> VectorRetriever:
    service = EmbeddingService(model=PolicyKeywordModel())
    return VectorRetriever(service, top_k=3)


def test_indexes_local_policy_chunks_and_returns_metadata(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    indexed_count = retriever.index_chunks(policy_chunks)

    results = retriever.retrieve("How do I reset my password?")

    assert indexed_count == len(policy_chunks)
    assert results
    assert any(result.metadata["policy_id"] == "POL-ACC-001" for result in results)
    assert results[0].text
    assert results[0].score > 0


def test_top_k_is_configurable_and_scores_are_ordered(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    retriever.index_chunks(policy_chunks)

    results = retriever.retrieve("What happens after a payment failure?", top_k=2)

    assert len(results) == 2
    assert all(results[index].score >= results[index + 1].score for index in range(len(results) - 1))


def test_retrieval_is_deterministic(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    retriever.index_chunks(policy_chunks)

    first = retriever.retrieve("What is the refund policy?", top_k=3)
    second = retriever.retrieve("What is the refund policy?", top_k=3)

    assert first == second


def test_empty_index_returns_no_chunks(retriever: VectorRetriever) -> None:
    assert retriever.retrieve("How do I reset my password?") == []


def test_category_filter_returns_matching_documents(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    retriever.index_chunks(policy_chunks)

    results = retriever.retrieve(
        "How do I reset my password?",
        filters={"category": "Identity and Access Management"},
    )

    assert results
    assert all(
        result.metadata.get("category", "").casefold() == "identity and access management"
        for result in results
    )


def test_status_filter_returns_matching_documents(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    retriever.index_chunks(policy_chunks)

    results = retriever.retrieve(
        "How do I reset my password?",
        filters={"status": "approved"},
    )

    assert results
    assert all(result.metadata.get("status", "").casefold() == "approved" for result in results)


def test_combined_filters_narrow_results(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    retriever.index_chunks(policy_chunks)

    results = retriever.retrieve(
        "How do I reset my password?",
        filters={
            "category": "Identity and Access Management",
            "status": "approved",
        },
    )

    assert results
    assert all(
        result.metadata.get("category", "").casefold() == "identity and access management"
        for result in results
    )
    assert all(result.metadata.get("status", "").casefold() == "approved" for result in results)


def test_no_matching_documents_are_returned_for_filter(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    retriever.index_chunks(policy_chunks)

    results = retriever.retrieve(
        "How do I reset my password?",
        filters={"department": "This Department Does Not Exist"},
    )

    assert results == []


def test_no_filters_returns_normal_retrieval_behavior(
    retriever: VectorRetriever, policy_chunks: list[object]
) -> None:
    retriever.index_chunks(policy_chunks)

    results = retriever.retrieve("How do I reset my password?")
    filtered_results = retriever.retrieve(
        "How do I reset my password?",
        filters=None,
    )

    assert results == filtered_results


def test_invalid_question_is_rejected(retriever: VectorRetriever) -> None:
    with pytest.raises(RetrieverError, match="non-empty"):
        retriever.retrieve("   ")