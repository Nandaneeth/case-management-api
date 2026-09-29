"""Deterministic, network-free LLM provider for local use and tests."""

from __future__ import annotations

from rag.generation.base import GenerationRequest, GenerationResult, LLMProvider


class MockLLMProvider(LLMProvider):
    """Return a deterministic answer while recording the latest request."""

    def __init__(self, response_template: str | None = None) -> None:
        self.response_template = response_template
        self.last_request: GenerationRequest | None = None

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.last_request = request
        text = self.response_template or (
            f"Mock grounded answer for '{request.query}' using "
            f"{len(request.context)} context chunks."
        )
        return GenerationResult(text=text, provider="mock")


__all__ = ["MockLLMProvider"]