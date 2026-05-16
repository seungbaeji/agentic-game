from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseModel):
    provider: str = Field(default="google")
    api_key: SecretStr | None = Field(default=None)
    model: str = Field(default="gemini-2.5-flash")
    temperature: float = Field(default=0)
    timeout_seconds: float = Field(default=30)
    max_retries: int = Field(default=2)


class UISettings(BaseModel):
    app_name: str = Field(default="agentic-game")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    llm: LLMSettings = Field(default_factory=LLMSettings)
    ui: UISettings = Field(default_factory=UISettings)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings loaded from environment and .env files."""
    return Settings()
