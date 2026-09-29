"""Provider-neutral contract for grounded text generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationRequest:
    """Inputs passed to a text-generation provider."""

    system_instructions: str
    grounded_context: str
    user_question: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.system_instructions, str) or not self.system_instructions.strip():
            raise ValueError("system_instructions must be a non-empty string")
        if not isinstance(self.grounded_context, str):
            raise TypeError("grounded_context must be a string")
        if not isinstance(self.user_question, str):
            raise TypeError("user_question must be a string")


class TextGenerator(ABC):
    """Interface implemented by concrete text-generation providers."""

    @abstractmethod
    def generate(
        self,
        *,
        system_instructions: str,
        grounded_context: str,
        user_question: str = "",
    ) -> str:
        """Generate text from instructions, grounded context, and an optional question."""
        raise NotImplementedError


__all__ = ["GenerationRequest", "TextGenerator"]