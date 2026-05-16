from __future__ import annotations

from agentic_game.application.ports import LLMPort
from agentic_game.config import Settings, get_settings
from agentic_game.errors import ConfigurationError
from agentic_game.outbound.llm.gemini import GeminiLLMAdapter
from agentic_game.outbound.llm.openai import OpenAILLMAdapter

_GEMINI_PROVIDERS = {"gemini", "google"}
_OPENAI_PROVIDERS = {"openai"}


def create_llm_adapter(settings: Settings | None = None) -> LLMPort:
    """Create the configured outbound LLM adapter."""
    resolved_settings = settings or get_settings()
    provider = resolved_settings.llm.provider.lower()

    if provider in _GEMINI_PROVIDERS:
        return GeminiLLMAdapter(resolved_settings)
    if provider in _OPENAI_PROVIDERS:
        return OpenAILLMAdapter(resolved_settings)

    supported_providers = sorted([*_GEMINI_PROVIDERS, *_OPENAI_PROVIDERS])
    raise ConfigurationError(
        f"지원하지 않는 LLM provider입니다: {provider}. "
        f"지원 목록: {', '.join(supported_providers)}"
    )
