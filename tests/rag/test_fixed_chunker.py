"""Tests for the fixed-size policy chunker."""

import pytest

from rag.chunking.fixed_chunker import ChunkerConfig, ChunkingConfigError, chunk_policy_document


def test_chunk_policy_document_splits_normal_document() -> None:
    text = "A" * 1200

    chunks = chunk_policy_document(text, policy_id="POL-001", source="policy.md")

    assert len(chunks) == 3
    assert all(chunk.text for chunk in chunks)
    assert chunks[0].start_index == 0
    assert chunks[0].end_index == 500
    assert chunks[1].start_index == 450
    assert chunks[1].end_index == 950
    assert chunks[2].start_index == 900
    assert chunks[2].end_index == 1200
    assert chunks[0].policy_id == "POL-001"
    assert chunks[0].source == "policy.md"


def test_chunk_policy_document_handles_short_document() -> None:
    text = "Short policy text."

    chunks = chunk_policy_document(text, policy_id="POL-002", source="short.md")

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].start_index == 0
    assert chunks[0].end_index == len(text)


def test_chunk_policy_document_creates_overlapping_chunks() -> None:
    text = "B" * 600

    chunks = chunk_policy_document(text, policy_id="POL-003", source="overlap.md", config=ChunkerConfig(chunk_size=200, overlap=50))

    assert len(chunks) == 4
    assert chunks[0].text == "B" * 200
    assert chunks[1].text == "B" * 200
    assert chunks[2].text == "B" * 200
    assert chunks[3].text == "B" * 150
    assert chunks[0].end_index == 200
    assert chunks[1].start_index == 150
    assert chunks[1].end_index == 350
    assert chunks[2].start_index == 300
    assert chunks[2].end_index == 500
    assert chunks[3].start_index == 450
    assert chunks[3].end_index == 600


def test_chunk_policy_document_rejects_invalid_configuration() -> None:
    with pytest.raises(ChunkingConfigError, match="chunk_size"):
        ChunkerConfig(chunk_size=0, overlap=10)

    with pytest.raises(ChunkingConfigError, match="overlap"):
        ChunkerConfig(chunk_size=100, overlap=100)

    with pytest.raises(ChunkingConfigError, match="overlap"):
        ChunkerConfig(chunk_size=100, overlap=-1)


def test_chunk_policy_document_preserves_metadata() -> None:
    text = "C" * 700
    metadata = {"category": "Access", "version": "2.1", "department": "Support"}

    chunks = chunk_policy_document(
        text,
        policy_id="POL-004",
        source="metadata.md",
        metadata=metadata,
    )

    assert all(chunk.metadata["category"] == "Access" for chunk in chunks)
    assert all(chunk.metadata["version"] == "2.1" for chunk in chunks)
    assert all(chunk.metadata["department"] == "Support" for chunk in chunks)
    assert all(chunk.policy_id == "POL-004" for chunk in chunks)
    assert all(chunk.source == "metadata.md" for chunk in chunks)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
