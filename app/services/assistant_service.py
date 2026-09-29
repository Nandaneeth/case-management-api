"""Application service for grounded policy assistant queries."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from fastapi import Request

from app.core.exceptions import AssistantRetrievalError, ProviderConfigurationError
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from rag.generation.config import GenerationSettings, settings as generation_settings
from rag.generation.mock import MockLLMProvider
from rag.service import RAGResponse, RAGService, RAGServiceError


logger = logging.getLogger(__name__)


class EmptyRetriever:
    """Safe default until a persisted policy index is configured."""

    def retrieve(
        self,
        question: str,
        top_k: int,
        filters: Mapping[str, Any] | None = None,
    ) -> list[Any]:
        return []


def _build_generation_provider(settings: GenerationSettings) -> MockLLMProvider:
    """Build the configured provider available in this local deployment."""
    if settings.provider.casefold() != "mock":
        raise ProviderConfigurationError(
            f"Generation provider '{settings.provider}' is not installed."
        )
    return MockLLMProvider()


class AssistantService:
    """Translate validated API requests into RAG service calls."""

    def __init__(
        self,
        rag_service: RAGService | None = None,
        *,
        retriever: Any | None = None,
    ) -> None:
        if rag_service is not None and retriever is not None:
            raise ValueError("Provide either rag_service or retriever, not both")
        self.rag_service = rag_service or RAGService(
            retriever if retriever is not None else EmptyRetriever(),
            _build_generation_provider(generation_settings),
        )

    def query(self, request: AssistantQueryRequest) -> AssistantQueryResponse:
        """Run a grounded query and expose a stable API response shape."""
        filters = {
            key: value
            for key, value in {
                "category": request.category,
                "policy_id": request.policy_id,
                "status": request.status,
            }.items()
            if value is not None
        }
        top_k = request.top_k or self.rag_service.top_k

        try:
            result = self.rag_service.answer(
                request.question,
                filters=filters or None,
                top_k=request.top_k,
            )
        except RAGServiceError as exc:
            raise AssistantRetrievalError(str(exc)) from exc
        except Exception as exc:
            raise AssistantRetrievalError("Unable to retrieve policy context") from exc

        logger.info(
            "assistant query completed",
            extra={
                "event": "assistant_query_completed",
                "question_length": len(request.question),
                "filters": filters,
                "top_k": top_k,
                "supported": result.supported,
                "source_count": len(result.sources),
            },
        )
        return self._to_response(result, filters=filters, top_k=top_k)

    @staticmethod
    def _to_response(
        result: RAGResponse,
        *,
        filters: dict[str, str],
        top_k: int,
    ) -> AssistantQueryResponse:
        return AssistantQueryResponse(
            answer=result.answer,
            supported=result.supported,
            sources=result.sources if result.supported else [],
            retrieval_metadata={
                "top_k_used": top_k,
                "filters": filters,
                "chunk_count": result.retrieved_chunks,
                "supported": result.supported,
            },
        )


def get_assistant_service(request: Request) -> AssistantService:
    """Provide the assistant service to the HTTP route."""
    service = getattr(request.app.state, "assistant_service", None)
    return service if service is not None else AssistantService()


__all__ = ["AssistantService", "EmptyRetriever", "get_assistant_service"]