"""Environment-backed settings for RAG generation providers."""

from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GenerationSettings(BaseSettings):
    """Runtime generation settings loaded from environment variables.

    The mock provider is the safe zero-configuration default. For providers
    that require authentication, ``API_KEY`` must be supplied by the runtime
    environment and is never given a source-code default.
    """

    provider: str = "mock"
    model_name: str | None = None
    api_key: str | None = None
    max_tokens: int = 512
    temperature: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_provider_credentials(self) -> "GenerationSettings":
        """Reject configured providers that require a missing API key."""
        if self.provider.casefold() in {"anthropic", "openai"} and not self.api_key:
            raise ValueError(
                f"API_KEY is required when PROVIDER is '{self.provider}'"
            )
        return self


settings = GenerationSettings()
GenerationConfig = GenerationSettings

__all__ = ["GenerationConfig", "GenerationSettings", "settings"]