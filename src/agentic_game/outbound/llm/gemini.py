from __future__ import annotations

from typing import TypeVar

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from agentic_game.config import Settings, get_settings
from agentic_game.errors import ConfigurationError, LLMError, LLMQuotaExceededError

T = TypeVar("T")


class GeminiLLMAdapter:
    def __init__(self, settings: Settings | None = None) -> None:
        """Create a Gemini-backed LLM adapter from application settings."""
        self._settings = settings or get_settings()
        api_key = self._settings.llm.api_key
        if api_key is None:
            raise ConfigurationError("LLM__API_KEY 환경 변수를 설정한 뒤 실행해 주세요.")

        llm = ChatGoogleGenerativeAI(
            model=self._settings.llm.model,
            temperature=self._settings.llm.temperature,
            google_api_key=api_key.get_secret_value(),
            timeout=self._settings.llm.timeout_seconds,
            max_retries=self._settings.llm.max_retries,
        )
        self._llm = llm

    def structured_output(self, schema: type[T], prompt: str) -> T:
        """Invoke Gemini and parse the response into the requested schema."""
        try:
            return self._llm.with_structured_output(schema).invoke(prompt)
        except ChatGoogleGenerativeAIError as exc:
            raise _to_llm_error(exc) from exc

    def respond(self, prompt: str) -> str:
        """Invoke Gemini and return a plain text response."""
        try:
            return str(self._llm.invoke(prompt).content)
        except ChatGoogleGenerativeAIError as exc:
            raise _to_llm_error(exc) from exc


def _to_llm_error(exc: ChatGoogleGenerativeAIError) -> LLMError:
    """Map Gemini provider errors to application-level LLM errors."""
    message = str(exc)
    if "RESOURCE_EXHAUSTED" in message or "429" in message:
        return LLMQuotaExceededError(message)
    return LLMError(message)
