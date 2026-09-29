"""Tests for the local vector-store abstraction."""

from pathlib import Path

import pytest

from rag.retrieval.vector_store import VectorStore, VectorStoreError


def test_inserting_chunks_and_searching_returns_scores() -> None:
    store = VectorStore()
    store.add_chunk("chunk-1", [1.0, 0.0], {"policy_id": "password-reset"})
    store.add_chunk("chunk-2", [0.0, 1.0], {"policy_id": "payment-failure"})

    matches = store.search([1.0, 0.0])

    assert matches[0].chunk_id == "chunk-1"
    assert matches[0].score == pytest.approx(1.0)
    assert matches[1].score == pytest.approx(0.0)


def test_top_k_limits_results() -> None:
    store = VectorStore(default_top_k=2)
    for index in range(3):
        store.add_chunk(f"chunk-{index}", [1.0, float(index + 1)], {"index": index})

    assert len(store.search([1.0, 1.0])) == 2
    assert len(store.search([1.0, 1.0], top_k=1)) == 1


def test_metadata_and_chunk_id_are_preserved() -> None:
    metadata = {"policy_id": "account-access", "source": "account_access_policy.md"}
    store = VectorStore()
    store.add_chunk("stable-chunk-id", [0.5, 0.5], metadata)

    match = store.search([0.5, 0.5])[0]

    assert match.chunk_id == "stable-chunk-id"
    assert match.metadata == metadata


def test_empty_index_returns_no_matches() -> None:
    store = VectorStore()

    assert store.search([1.0, 0.0]) == []


def test_index_can_be_saved_and_loaded(tmp_path: Path) -> None:
    path = tmp_path / "vectors.json"
    store = VectorStore(default_top_k=1)
    store.add_chunk("chunk-1", [1.0, 0.0], {"policy_id": "password-reset"})

    store.save(path)
    loaded = VectorStore.load(path)

    assert loaded.search([1.0, 0.0])[0].chunk_id == "chunk-1"
    assert loaded.search([1.0, 0.0])[0].metadata["policy_id"] == "password-reset"


def test_mismatched_dimensions_are_rejected() -> None:
    store = VectorStore()
    store.add_chunk("chunk-1", [1.0, 0.0], {})

    with pytest.raises(VectorStoreError, match="dimension"):
        store.add_chunk("chunk-2", [1.0, 0.0, 0.0], {})