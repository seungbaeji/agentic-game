from __future__ import annotations


class AgenticGameError(Exception):
    user_message = "요청 처리 중 오류가 발생했습니다."


class ConfigurationError(AgenticGameError):
    user_message = "설정이 올바르지 않습니다."


class LLMError(AgenticGameError):
    user_message = "LLM 호출 중 오류가 발생했습니다. 잠시 뒤 다시 시도해 주세요."


class LLMQuotaExceededError(LLMError):
    user_message = "LLM 사용량 한도에 도달했습니다. 잠시 뒤 다시 시도해 주세요."
