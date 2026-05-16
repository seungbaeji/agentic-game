from __future__ import annotations

import pytest
from pydantic import SecretStr

from agentic_game.agent.decisions import BattleDecision
from agentic_game.config.settings import Settings
from agentic_game.domain.battle import BattleEvent
from agentic_game.outbound.llm.testing import TestingLLMAdapter


def test_settings_loads_llm_api_key_as_secret() -> None:
    settings = Settings(_env_file=None, llm={"api_key": "super-secret"})

    assert isinstance(settings.llm.api_key, SecretStr)
    assert str(settings.llm.api_key) == "**********"
    assert settings.llm.api_key.get_secret_value() == "super-secret"


def test_testing_llm_adapter_validates_structured_output_dicts() -> None:
    llm = TestingLLMAdapter(
        structured_outputs={
            BattleDecision: [
                {
                    "event": BattleEvent.ATTACK.value,
                    "reason": "user wants to attack",
                }
            ]
        }
    )

    decision = llm.structured_output(BattleDecision, "prompt")

    assert decision.event == BattleEvent.ATTACK
    assert decision.reason == "user wants to attack"


def test_testing_llm_adapter_fails_when_output_is_missing() -> None:
    llm = TestingLLMAdapter()

    with pytest.raises(RuntimeError, match="No testing structured output"):
        llm.structured_output(BattleDecision, "prompt")
