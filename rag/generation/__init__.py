"""Provider-neutral generation interfaces and local test implementations."""

from .config import GenerationConfig
from .mock import MockLLMProvider
from .mock_provider import MockTextGenerator
from .provider import GenerationRequest as LegacyGenerationRequest, TextGenerator
from .base import GenerationRequest, GenerationResult, LLMProvider

__all__ = [
	"GenerationConfig",
	"GenerationRequest",
	"GenerationResult",
	"LLMProvider",
	"MockLLMProvider",
	"MockTextGenerator",
	"LegacyGenerationRequest",
	"TextGenerator",
]
