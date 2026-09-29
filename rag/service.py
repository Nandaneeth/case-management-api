"""Framework-independent orchestration for the local policy RAG pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from rag.generation.base import GenerationRequest, GenerationResult, LLMProvider
from rag.generation.context_builder import ContextBuilder, ContextBuilderError
from rag.retrieval.reranker import Reranker


class RAGServiceError(ValueError):
    """Raised when the RAG service receives invalid configuration or input."""


@dataclass(frozen=True)
class RAGResponse:
    """Structured result returned by :class:`RAGService`."""

    answer: str
    supported: bool
    explanation: str
    sources: list[str] = field(default_factory=list)
    context: str = ""
    retrieved_chunks: int = 0


class RAGService:
    """Coordinate retrieval, evidence screening, context building, and generation."""

    def __init__(
        self,
        vector_retriever: Any,
        generation_provider: LLMProvider,
        *,
        hybrid_retriever: Any | None = None,
        retrieval_mode: str = "vector",
        reranker: Reranker | None = None,
        context_builder: ContextBuilder | None = None,
        top_k: int = 5,
        max_context_chunks: int = 5,
        min_similarity_score: float = 0.5,
        system_instructions: str = "Answer only from the supplied policy context.",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> None:
        if retrieval_mode not in {"vector", "hybrid"}:
            raise RAGServiceError("retrieval_mode must be 'vector' or 'hybrid'")
        if retrieval_mode == "hybrid" and hybrid_retriever is None:
            raise RAGServiceError("hybrid_retriever is required when retrieval_mode is 'hybrid'")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise RAGServiceError("top_k must be a positive integer")
        if (
            not isinstance(max_context_chunks, int)
            or isinstance(max_context_chunks, bool)
            or max_context_chunks <= 0
        ):
            raise RAGServiceError("max_context_chunks must be a positive integer")
        if (
            not isinstance(min_similarity_score, (int, float))
            or isinstance(min_similarity_score, bool)
            or not math.isfinite(float(min_similarity_score))
            or not 0 <= min_similarity_score <= 1
        ):
            raise RAGServiceError("min_similarity_score must be a finite number from 0 to 1")
        if not isinstance(system_instructions, str) or not system_instructions.strip():
            raise RAGServiceError("system_instructions must be a non-empty string")
        if not hasattr(generation_provider, "generate"):
            raise RAGServiceError("generation_provider must implement generate")

        self.vector_retriever = vector_retriever
        self.hybrid_retriever = hybrid_retriever
        self.generation_provider = generation_provider
        self.retrieval_mode = retrieval_mode
        self.reranker = reranker or Reranker()
        self.context_builder = context_builder or ContextBuilder(max_chunks=max_context_chunks)
        self.top_k = top_k
        self.max_context_chunks = max_context_chunks
        self.min_similarity_score = float(min_similarity_score)
        self.system_instructions = system_instructions.strip()
        self.max_tokens = max_tokens
        self.temperature = temperature

    def answer(
        self,
        question: str,
        *,
        filters: Mapping[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RAGResponse:
        """Answer a question only when retrieved evidence clears the threshold."""
        if not isinstance(question, str) or not question.strip():
            raise RAGServiceError("question must be a non-empty string")
        if filters is not None and not isinstance(filters, Mapping):
            raise RAGServiceError("filters must be a mapping of metadata fields to values")
        if top_k is not None and (
            not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0
        ):
            raise RAGServiceError("top_k must be a positive integer")

        effective_top_k = self.top_k if top_k is None else top_k

        candidates = self._retriever().retrieve(
            question.strip(),
            top_k=effective_top_k,
            filters=filters,
        )
        if not candidates:
            return self._refusal("No policy context was retrieved for this question.")

        eligible = [candidate for candidate in candidates if self._meets_threshold(candidate)]
        if not eligible:
            return self._refusal(
                "The available policy context is insufficient: no retrieved evidence "
                f"reached the configured similarity threshold of {self.min_similarity_score:.2f}."
            )

        reranked = self.reranker.rerank(question.strip(), eligible, top_k=effective_top_k)
        try:
            context = self.context_builder.build(
                reranked,
                max_chunks=self.max_context_chunks,
            )
        except ContextBuilderError:
            return self._refusal("The available policy context is insufficient for a grounded answer.")
        if not context.strip():
            return self._refusal("The available policy context is insufficient for a grounded answer.")

        result = self.generation_provider.generate(
            GenerationRequest(
                system_instructions=self.system_instructions,
                context=tuple(self._candidate_text(candidate) for candidate in reranked),
                query=question.strip(),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        )
        if not isinstance(result, GenerationResult):
            raise RAGServiceError("generation_provider returned an invalid result")
        if not isinstance(result.text, str) or not result.text.strip():
            return self._refusal("The generation provider did not return a grounded answer.")

        return RAGResponse(
            answer=result.text.strip(),
            supported=True,
            explanation="The answer was generated from retrieved policy context meeting the evidence threshold.",
            sources=self._sources(reranked),
            context=context,
            retrieved_chunks=len(reranked),
        )

    def _retriever(self) -> Any:
        if self.retrieval_mode == "hybrid":
            return self.hybrid_retriever
        return self.vector_retriever

    def _meets_threshold(self, candidate: Any) -> bool:
        score = getattr(candidate, "score", None)
        return (
            isinstance(score, (int, float))
            and not isinstance(score, bool)
            and math.isfinite(float(score))
            and float(score) >= self.min_similarity_score
        )

    @staticmethod
    def _candidate_text(candidate: Any) -> str:
        return getattr(candidate, "text", "")

    @staticmethod
    def _sources(candidates: list[Any]) -> list[str]:
        citations: list[str] = []
        for candidate in candidates:
            metadata = getattr(candidate, "metadata", {}) or {}
            source = metadata.get("source")
            policy_id = metadata.get("policy_id")
            if not source:
                continue
            citation = f"{source} ({policy_id})" if policy_id else str(source)
            if citation not in citations:
                citations.append(citation)
        return citations

    @staticmethod
    def _refusal(explanation: str) -> RAGResponse:
        return RAGResponse(answer="", supported=False, explanation=explanation)


__all__ = ["RAGResponse", "RAGService", "RAGServiceError"]