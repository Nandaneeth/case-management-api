"""Grounded prompt templates for policy-aware retrieval-augmented generation.

The prompt is intentionally provider-agnostic: it only defines the instruction
contract that a downstream model should follow. That keeps the template reusable
across local, hosted, or third-party LLM integrations without hard-coding any
single provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class PromptTemplate:
    """Configurable structural prompt for grounded RAG answers."""

    system_instructions: str = (
        "You are a careful policy assistant. Answer only from the supplied policy context. "
        "Do not use outside knowledge or assume undocumented policy rules. "
        "If the context is insufficient, say so clearly and avoid guessing. "
        "Never invent policy information, dates, exceptions, or requirements. "
        "Cite the policy source(s) used in your answer. "
        "Distinguish between explicit policy requirements and explanatory background text. "
        "Use only the supplied context when answering."
    )
    answer_format: str = (
        "Provide a concise answer grounded in the supplied policy context. "
        "Use sections: 'Answer', 'Policy requirements', 'Sources', and 'Insufficient context' "
        "only when needed."
    )

    def render(self, question: str, context: str) -> str:
        """Render a client-agnostic prompt from a user question and retrieved context."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        if not isinstance(context, str):
            raise TypeError("context must be a string")

        return (
            f"System instructions:\n{self.system_instructions}\n\n"
            f"Question:\n{question.strip()}\n\n"
            f"Supplied policy context:\n{context.strip()}\n\n"
            f"Response instructions:\n{self.answer_format}\n\n"
            "Requirements:\n"
            "1. Answer only using the supplied policy context.\n"
            "2. Never invent policy information or make unsupported claims.\n"
            "3. If the context is insufficient, state that explicitly and explain what is missing.\n"
            "4. Cite the policy source(s) used.\n"
            "5. Separate policy requirements from explanatory background text.\n"
            "6. Do not use knowledge from outside the supplied context.\n"
        )


class GroundedPromptFactory:
    """Factory that keeps the prompt template configurable and testable."""

    def __init__(self, template: PromptTemplate | None = None) -> None:
        self.template = template or PromptTemplate()

    def create(self, question: str, context: str) -> str:
        """Create the final prompt for a grounded answer request."""
        return self.template.render(question=question, context=context)

    def with_template(self, template: PromptTemplate) -> "GroundedPromptFactory":
        """Return a new factory configured with a different template."""
        if not isinstance(template, PromptTemplate):
            raise TypeError("template must be a PromptTemplate")
        return GroundedPromptFactory(template=template)


def build_grounded_prompt(question: str, context: str, *, template: PromptTemplate | None = None) -> str:
    """Convenience helper for building a grounded prompt with optional template configuration."""
    factory = GroundedPromptFactory(template=template)
    return factory.create(question, context)


__all__ = ["GroundedPromptFactory", "PromptTemplate", "build_grounded_prompt"]
