from __future__ import annotations

import pytest
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from agentic_game.agent.decisions import BattleDecision
from agentic_game.config.settings import Settings
from agentic_game.errors import ConfigurationError, LLMQuotaExceededError
from agentic_game.inbound.cli.main import format_app_error
from agentic_game.outbound.llm.gemini import GeminiLLMAdapter


class FailingStructuredLLM:
    def invoke(self, prompt: str) -> None:
        raise ChatGoogleGenerativeAIError("429 RESOURCE_EXHAUSTED")


class FailingLLM:
    def with_structured_output(self, schema: type[object]) -> FailingStructuredLLM:
        return FailingStructuredLLM()

    def invoke(self, prompt: str) -> None:
        raise ChatGoogleGenerativeAIError("429 RESOURCE_EXHAUSTED")


def test_gemini_adapter_requires_api_key_with_app_error() -> None:
    with pytest.raises(ConfigurationError):
        GeminiLLMAdapter(Settings(_env_file=None, llm={"api_key": None}))


def test_gemini_adapter_wraps_structured_quota_error() -> None:
    adapter = GeminiLLMAdapter.__new__(GeminiLLMAdapter)
    adapter._llm = FailingLLM()

    with pytest.raises(LLMQuotaExceededError):
        adapter.structured_output(BattleDecision, "prompt")


def test_gemini_adapter_wraps_response_quota_error() -> None:
    adapter = GeminiLLMAdapter.__new__(GeminiLLMAdapter)
    adapter._llm = FailingLLM()

    with pytest.raises(LLMQuotaExceededError):
        adapter.respond("prompt")


def test_cli_formats_app_error_without_provider_details() -> None:
    message = format_app_error(LLMQuotaExceededError("429 RESOURCE_EXHAUSTED provider details"))

    assert message == "LLM 사용량 한도에 도달했습니다. 잠시 뒤 다시 시도해 주세요."
    assert "RESOURCE_EXHAUSTED" not in message
