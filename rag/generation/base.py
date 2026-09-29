"""Provider-neutral interfaces for RAG text generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationRequest:
    """Input supplied to an LLM provider for one grounded generation request."""

    system_instructions: str
    context: tuple[str, ...]
    query: str
    max_tokens: int | None = None
    temperature: float | None = None


@dataclass(frozen=True)
class GenerationResult:
    """Provider-independent result returned from a generation request."""

    text: str
    provider: str
    raw_response: dict | None = None


class LLMProvider(ABC):
    """Abstract interface implemented by each concrete LLM provider."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate text from the request's instructions, context, and query."""
        raise NotImplementedError


__all__ = ["GenerationRequest", "GenerationResult", "LLMProvider"]