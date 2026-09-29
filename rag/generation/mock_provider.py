"""Deterministic generation provider for tests and local development."""

from __future__ import annotations

from .provider import GenerationRequest, TextGenerator


class MockTextGenerator(TextGenerator):
    """Return a configured response while recording the latest request."""

    def __init__(self, response: str = "Mock generated response") -> None:
        if not isinstance(response, str):
            raise TypeError("response must be a string")
        self.response = response
        self.last_request: GenerationRequest | None = None

    def generate(
        self,
        *,
        system_instructions: str,
        grounded_context: str,
        user_question: str = "",
    ) -> str:
        self.last_request = GenerationRequest(
            system_instructions=system_instructions,
            grounded_context=grounded_context,
            user_question=user_question,
        )
        return self.response


__all__ = ["MockTextGenerator"]