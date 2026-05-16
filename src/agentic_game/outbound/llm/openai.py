from __future__ import annotations

from typing import TypeVar

from langchain_openai import ChatOpenAI
from openai import OpenAIError, RateLimitError

from agentic_game.config import Settings, get_settings
from agentic_game.errors import ConfigurationError, LLMError, LLMQuotaExceededError

T = TypeVar("T")


class OpenAILLMAdapter:
    def __init__(self, settings: Settings | None = None) -> None:
        """Create an OpenAI-backed LLM adapter from application settings."""
        self._settings = settings or get_settings()
        api_key = self._settings.llm.api_key
        if api_key is None:
            raise ConfigurationError("LLM__API_KEY 환경 변수를 설정한 뒤 실행해 주세요.")

        self._llm = ChatOpenAI(
            model=self._settings.llm.model,
            temperature=self._settings.llm.temperature,
            api_key=api_key.get_secret_value(),
            timeout=self._settings.llm.timeout_seconds,
            max_retries=self._settings.llm.max_retries,
        )

    def structured_output(self, schema: type[T], prompt: str) -> T:
        """Invoke OpenAI and parse the response into the requested schema."""
        try:
            return self._llm.with_structured_output(schema).invoke(prompt)
        except RateLimitError as exc:
            raise LLMQuotaExceededError(str(exc)) from exc
        except OpenAIError as exc:
            raise LLMError(str(exc)) from exc

    def respond(self, prompt: str) -> str:
        """Invoke OpenAI and return a plain text response."""
        try:
            return str(self._llm.invoke(prompt).content)
        except RateLimitError as exc:
            raise LLMQuotaExceededError(str(exc)) from exc
        except OpenAIError as exc:
            raise LLMError(str(exc)) from exc
