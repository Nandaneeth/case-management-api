"""Tests for the provider abstraction and environment-backed configuration."""

import pytest

from rag.generation import GenerationConfig, MockTextGenerator


def test_mock_generator_returns_response_and_records_grounding() -> None:
    generator = MockTextGenerator(response="Grounded answer")

    result = generator.generate(
        system_instructions="Use policy context only.",
        grounded_context="Policy P-1 requires verification.",
        user_question="What is required?",
    )

    assert result == "Grounded answer"
    assert generator.last_request is not None
    assert generator.last_request.grounded_context == "Policy P-1 requires verification."
    assert generator.last_request.user_question == "What is required?"


def test_generation_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_LLM_PROVIDER", "local")
    monkeypatch.setenv("TEST_LLM_MODEL_NAME", "policy-model")
    monkeypatch.setenv("TEST_LLM_API_KEY", "secret-from-environment")
    monkeypatch.setenv("TEST_LLM_MAX_TOKENS", "256")
    monkeypatch.setenv("TEST_LLM_TEMPERATURE", "0.2")

    config = GenerationConfig(_env_prefix="TEST_LLM_")

    assert config.provider == "local"
    assert config.model_name == "policy-model"
    assert config.api_key == "secret-from-environment"
    assert config.max_tokens == 256
    assert config.temperature == 0.2


def test_generation_request_rejects_missing_system_instructions() -> None:
    generator = MockTextGenerator()

    with pytest.raises(ValueError, match="system_instructions"):
        generator.generate(system_instructions="", grounded_context="context")