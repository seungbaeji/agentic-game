from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field

from agentic_game.application.ports import LLMPort


class CraftNarration(BaseModel):
    response: str = Field(description="User-facing craft result narration.")


def build_craft_narration_prompt(
    *,
    raw: Mapping[str, Any],
    llm_payload: Mapping[str, Any],
) -> str:
    """Build a prompt for craft result flavor text."""
    return (
        "제작 결과를 한국어 한 문장으로 자연스럽게 변주해 주세요.\n"
        "게임 상태 변경은 이미 확정되어 있으므로 수량, 아이템, 성공 여부를 바꾸지 마세요.\n"
        f"raw={dict(raw)}\n"
        f"summary={llm_payload.get('summary', '')}"
    )


def generate_craft_narration(
    *,
    llm: LLMPort,
    raw: Mapping[str, Any],
    llm_payload: Mapping[str, Any],
) -> str | None:
    """Generate optional craft narration, falling back to deterministic summary."""
    try:
        narration = llm.structured_output(
            CraftNarration,
            build_craft_narration_prompt(raw=raw, llm_payload=llm_payload),
        )
    except Exception:
        return None

    return narration.response.strip() or None
