"""Tests for lightweight keyword-based retrieval over policy chunks."""

from pathlib import Path

import pytest

from rag.chunking.fixed_chunker import ChunkerConfig, chunk_policy_document
from rag.ingestion.document_loader import load_policy_documents
from rag.retrieval.keyword_retriever import KeywordRetrievalError, KeywordRetriever


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
def retriever(policy_chunks: list[object]) -> KeywordRetriever:
    return KeywordRetriever(policy_chunks, top_k=3)


def test_keyword_retrieval_ranks_relevant_policy_first(
    retriever: KeywordRetriever,
) -> None:
    results = retriever.retrieve("How do I reset my password?", top_k=3)

    assert results
    assert results[0].metadata["policy_id"] == "POL-ACC-001"
    assert results[0].score > 0
    assert results[0].text


def test_top_k_limits_results(retriever: KeywordRetriever) -> None:
    results = retriever.retrieve("password reset", top_k=1)

    assert len(results) == 1
    assert results[0].score > 0


def test_metadata_is_preserved(retriever: KeywordRetriever) -> None:
    results = retriever.retrieve("payment failure", top_k=2)

    assert results
    assert all("policy_id" in result.metadata for result in results)
    assert all("category" in result.metadata for result in results)


def test_no_matching_terms_returns_empty_list(retriever: KeywordRetriever) -> None:
    results = retriever.retrieve("quantum alien spaceship telemetry", top_k=5)

    assert results == []


def test_invalid_query_is_rejected(retriever: KeywordRetriever) -> None:
    with pytest.raises(KeywordRetrievalError, match="non-empty"):
        retriever.retrieve("   ")
