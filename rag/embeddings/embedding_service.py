"""Reusable text embedding service for local policy retrieval workflows.

This module is intentionally limited to model loading and embedding generation. It
keeps model instantiation separate from document and query embedding logic so the
service can be reused by higher-level retrieval or evaluation code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingServiceError(RuntimeError):
    """Raised when the embedding service cannot load or use its model."""


@dataclass(frozen=True)
class EmbeddingService:
    """Generate normalized local embeddings with SentenceTransformers."""

    model_name: str = DEFAULT_MODEL_NAME
    model: Any = None

    def __post_init__(self) -> None:
        """Ensure the embedding model is available and initialized."""
        if self.model is None:
            object.__setattr__(self, "model", self._load_model(self.model_name))

    @staticmethod
    def _load_model(model_name: str) -> Any:
        """Load the sentence-transformers model by name."""
        if not model_name or not isinstance(model_name, str):
            raise EmbeddingServiceError("model_name must be a non-empty string")

        try:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(model_name)
        except Exception as exc:  # pragma: no cover - depends on local model downloads
            raise EmbeddingServiceError(
                f"Unable to load embedding model '{model_name}'. "
                "Install sentence-transformers and ensure the model is available."
            ) from exc

    @property
    def dimension(self) -> int:
        """Return the dimension reported by the loaded model."""
        if self.model is None:
            raise EmbeddingServiceError("Embedding model is not loaded")
        try:
            dimension = int(self.model.get_sentence_embedding_dimension())
        except Exception as exc:
            raise EmbeddingServiceError("Unable to determine embedding dimension") from exc
        if dimension <= 0:
            raise EmbeddingServiceError("Embedding model reported an invalid dimension")
        return dimension

    def _embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode texts and validate the returned vector dimensions."""
        if not isinstance(texts, Sequence) or isinstance(texts, (str, bytes)):
            raise EmbeddingServiceError("texts must be a sequence of strings")
        if not texts:
            raise EmbeddingServiceError("Embedding batch cannot be empty")
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise EmbeddingServiceError("Every text must be a non-empty string")

        try:
            vectors: Any = self.model.encode(
                list(texts), normalize_embeddings=True, batch_size=32
            )
        except Exception as exc:
            raise EmbeddingServiceError("Embedding generation failed") from exc

        try:
            result = [[float(value) for value in vector] for vector in vectors]
        except (TypeError, ValueError) as exc:
            raise EmbeddingServiceError("Model returned invalid embedding vectors") from exc
        if len(result) != len(texts):
            raise EmbeddingServiceError("Model returned an unexpected number of vectors")
        if any(len(vector) != self.dimension for vector in result):
            raise EmbeddingServiceError("Model returned inconsistent vector dimensions")
        return result

    def embed_document(self, text: str) -> list[float]:
        """Embed one policy document or chunk."""
        return self._embed_texts([text])[0]

    def embed_query(self, query: str) -> list[float]:
        """Embed one user query with the same model as policy documents."""
        return self._embed_texts([query])[0]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple texts while preserving their input order."""
        return self._embed_texts(texts)


__all__ = [
    "DEFAULT_MODEL_NAME",
    "EmbeddingService",
    "EmbeddingServiceError",
]
