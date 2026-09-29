"""Tests for the grounded RAG prompt template."""

from rag.generation.prompts import GroundedPromptFactory, PromptTemplate, build_grounded_prompt


def test_prompt_renders_grounded_instructions() -> None:
    prompt = build_grounded_prompt(
        "What steps are required to reset a password?",
        "Policy ID: POL-ACC-001\nSource: Internal Policy Library / Identity & Access Management\nText: Verify identity before resetting.",
    )

    assert "Answer only using the supplied policy context" in prompt
    assert "Never invent policy information" in prompt
    assert "If the context is insufficient" in prompt
    assert "Cite the policy source(s) used" in prompt
    assert "Distinguish between explicit policy requirements" in prompt
    assert "Do not use knowledge from outside the supplied context" in prompt
    assert "What steps are required to reset a password?" in prompt
    assert "Policy ID: POL-ACC-001" in prompt


def test_prompt_template_is_configurable() -> None:
    custom_template = PromptTemplate(
        system_instructions="Use only the local policy record.",
        answer_format="Answer in JSON.",
    )

    prompt = GroundedPromptFactory(template=custom_template).create(
        "What does this policy say?",
        "Context text here.",
    )

    assert "Use only the local policy record." in prompt
    assert "Answer in JSON." in prompt


def test_prompt_rejects_invalid_question() -> None:
    try:
        build_grounded_prompt("   ", "context")
        raise AssertionError("Expected ValueError for empty question")
    except ValueError:
        pass
