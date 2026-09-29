"""Embedding-backed retrieval of policy chunks from a local vector store."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from rag.embeddings.embedding_service import EmbeddingService
from rag.retrieval.vector_store import VectorMatch, VectorStore, VectorStoreError


class RetrieverError(ValueError):
    """Raised when a retriever operation receives invalid input."""


@dataclass(frozen=True)
class RetrievedChunk:
    """A policy chunk returned by vector similarity search."""

    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]


class VectorRetriever:
    """Connect an embedding service to a local vector store."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore | None = None,
        top_k: int = 5,
    ) -> None:
        if not isinstance(embedding_service, EmbeddingService):
            raise RetrieverError("embedding_service must be an EmbeddingService")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise RetrieverError("top_k must be a positive integer")

        self.embedding_service = embedding_service
        self.vector_store = vector_store or VectorStore(default_top_k=top_k)
        self.top_k = top_k

    def index_chunks(self, chunks: Iterable[Any]) -> int:
        """Embed and index chunks, returning the number of chunks indexed."""
        chunk_list = list(chunks)
        if not chunk_list:
            return 0

        texts = [self._chunk_text(chunk) for chunk in chunk_list]
        embeddings = self.embedding_service.embed_batch(texts)
        if len(embeddings) != len(chunk_list):
            raise RetrieverError("Embedding service returned an unexpected number of vectors")

        for chunk, embedding in zip(chunk_list, embeddings):
            self.vector_store.add_chunk(
                chunk_id=self._chunk_id(chunk),
                embedding=embedding,
                metadata=self._chunk_metadata(chunk),
            )
        return len(chunk_list)

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        filters: Mapping[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> list[RetrievedChunk]:
        """Embed a user question and return the highest-scoring policy chunks."""
        if not isinstance(question, str) or not question.strip():
            raise RetrieverError("question must be a non-empty string")
        if top_k is not None and (
            not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0
        ):
            raise RetrieverError("top_k must be a positive integer")

        normalized_filters = self._normalize_filters(filters, **filter_kwargs)
        query_embedding = self.embedding_service.embed_query(question)
        try:
            matches = self.vector_store.search(
                query_embedding,
                top_k=self.top_k if top_k is None else top_k,
                filters=normalized_filters or None,
            )
        except VectorStoreError as exc:
            raise RetrieverError("Unable to search the vector store") from exc

        return [self._to_retrieved_chunk(match) for match in matches]

    @staticmethod
    def _normalize_filters(
        filters: Mapping[str, Any] | None = None,
        **filter_kwargs: Any,
    ) -> dict[str, str]:
        merged: dict[str, Any] = {}
        if filters is not None:
            if not isinstance(filters, Mapping):
                raise RetrieverError("filters must be a mapping of metadata fields to values")
            merged.update(dict(filters))
        merged.update(filter_kwargs)

        if not merged:
            return {}

        allowed_fields = {"category", "policy_id", "version", "status", "department"}
        normalized: dict[str, str] = {}
        invalid_fields = []

        for raw_key, raw_value in merged.items():
            field_name = str(raw_key).strip()
            if not field_name:
                raise RetrieverError("Filter field names must be non-empty strings")
            normalized_key = field_name.casefold()
            if normalized_key not in allowed_fields:
                invalid_fields.append(field_name)
                continue
            if raw_value is None:
                raise RetrieverError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized_value = str(raw_value).strip()
            if not normalized_value:
                raise RetrieverError(f"Filter value for '{field_name}' must be a non-empty string")
            normalized[normalized_key] = normalized_value

        if invalid_fields:
            invalid = ", ".join(sorted(set(invalid_fields)))
            raise RetrieverError(
                "Unsupported filter fields: "
                f"{invalid}. Allowed fields are: category, policy_id, version, status, department"
            )
        return normalized

    @staticmethod
    def _chunk_id(chunk: Any) -> str:
        chunk_id = getattr(chunk, "chunk_id", None)
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise RetrieverError("Each chunk must have a non-empty chunk_id")
        return chunk_id

    @staticmethod
    def _chunk_text(chunk: Any) -> str:
        text = getattr(chunk, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise RetrieverError("Each chunk must have non-empty text")
        return text

    @classmethod
    def _chunk_metadata(cls, chunk: Any) -> dict[str, Any]:
        metadata = getattr(chunk, "metadata", {})
        if not isinstance(metadata, Mapping):
            raise RetrieverError("Chunk metadata must be a mapping")

        result = dict(metadata)
        for field_name in ("policy_id", "source", "section"):
            value = getattr(chunk, field_name, None)
            if value is not None:
                result.setdefault(field_name, value)
        result["text"] = cls._chunk_text(chunk)
        return result

    @staticmethod
    def _to_retrieved_chunk(match: VectorMatch) -> RetrievedChunk:
        metadata = dict(match.metadata)
        text = metadata.pop("text", "")
        return RetrievedChunk(
            chunk_id=match.chunk_id,
            score=match.score,
            text=text,
            metadata=metadata,
        )


__all__ = ["RetrievedChunk", "RetrieverError", "VectorRetriever"]