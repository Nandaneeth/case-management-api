"""Focused tests for the reusable embedding service."""

from hashlib import sha256
from typing import Sequence

import pytest

from rag.embeddings.embedding_service import EmbeddingService, EmbeddingServiceError


class FakeEmbeddingModel:
    """Deterministic test double for the SentenceTransformer model."""

    def get_sentence_embedding_dimension(self) -> int:
        return 4

    def encode(self, texts: Sequence[str], **_: object) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    @staticmethod
    def _vector(text: str) -> list[float]:
        digest = sha256(text.encode("utf-8")).digest()
        return [byte / 255.0 for byte in digest[:4]]


@pytest.fixture
def embedding_service() -> EmbeddingService:
    return EmbeddingService(model=FakeEmbeddingModel())


def test_embedding_generation_and_dimension(embedding_service: EmbeddingService) -> None:
    vector = embedding_service.embed_document("Password reset and account recovery policy")

    assert vector
    assert all(isinstance(value, float) for value in vector)
    assert len(vector) == embedding_service.dimension


def test_batch_embedding_preserves_order_and_dimension(embedding_service: EmbeddingService) -> None:
    batch = [
        "Password reset requires a secure verification challenge.",
        "Payment failures may be caused by expired cards or bank rejections.",
        "Service outages should be communicated with a clear restoration timeline.",
    ]

    vectors = embedding_service.embed_batch(batch)

    assert len(vectors) == len(batch)
    assert vectors == [embedding_service.embed_document(text) for text in batch]
    assert all(len(vector) == embedding_service.dimension for vector in vectors)


def test_query_and_document_embeddings_have_compatible_dimensions(embedding_service: EmbeddingService) -> None:
    query = embedding_service.embed_query("Can I access my account after a reset?")
    policy_chunk = embedding_service.embed_document(
        "Account access is only granted after identity verification and authorization checks are complete."
    )

    assert len(query) == len(policy_chunk)
    assert len(query) == embedding_service.dimension


def test_embedding_is_deterministic(embedding_service: EmbeddingService) -> None:
    text = "Password reset requires identity verification."

    assert embedding_service.embed_document(text) == embedding_service.embed_document(text)


@pytest.mark.parametrize("method_name", ["embed_document", "embed_query"])
def test_empty_single_text_is_rejected(
    embedding_service: EmbeddingService, method_name: str
) -> None:
    with pytest.raises(EmbeddingServiceError, match="non-empty"):
        getattr(embedding_service, method_name)("   ")


def test_empty_batch_is_rejected(embedding_service: EmbeddingService) -> None:
    with pytest.raises(EmbeddingServiceError, match="cannot be empty"):
        embedding_service.embed_batch([])
