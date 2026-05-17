from __future__ import annotations

from typing import Any

from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.flow.models import (
    AvailableActions,
    ToolBinding,
    TransitionRule,
    tool_action_metadata,
)
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type LatestCraftResult = dict[str, Any]


type CraftTransitionRule = TransitionRule[CraftPhase, CraftEvent]


CRAFT_TRANSITIONS: list[CraftTransitionRule] = [
    TransitionRule(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CONTINUE,
        CraftPhase.CRAFT,
        "제작 단계로 이동",
        "제작할 아이템을 선택합니다.",
    ),
    TransitionRule(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CRAFT_POTION,
        CraftPhase.RESULT,
        "포션 제작",
        "제작을 시작하고 곧바로 회복 포션 제작을 시도합니다.",
    ),
    TransitionRule(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CRAFT_SWORD,
        CraftPhase.RESULT,
        "검 제작",
        "제작을 시작하고 곧바로 낡은 검 제작을 시도합니다.",
    ),
    TransitionRule(
        CraftPhase.CRAFT,
        CraftEvent.CRAFT_POTION,
        CraftPhase.RESULT,
        "포션 제작",
        "회복 포션 제작을 시도합니다.",
    ),
    TransitionRule(
        CraftPhase.CRAFT,
        CraftEvent.CRAFT_SWORD,
        CraftPhase.RESULT,
        "검 제작",
        "낡은 검 제작을 시도합니다.",
    ),
    TransitionRule(
        CraftPhase.RESULT,
        CraftEvent.RETRY,
        CraftPhase.CRAFT,
        "다시 제작",
        "제작 결과를 보고 다시 제작합니다.",
    ),
    TransitionRule(
        CraftPhase.RESULT,
        CraftEvent.COMPLETE,
        CraftPhase.COMPLETE,
        "제작 종료",
        "제작 업무를 종료합니다.",
    ),
]

CRAFT_TOOL_BINDINGS: dict[CraftEvent, ToolBinding[CraftEvent]] = {
    CraftEvent.CRAFT_POTION: ToolBinding(
        event=CraftEvent.CRAFT_POTION,
        tool_name="craft_item_tool",
        tool_input={"recipe": "potion"},
        state_effect="healing_potion can be added to inventory on success.",
    ),
    CraftEvent.CRAFT_SWORD: ToolBinding(
        event=CraftEvent.CRAFT_SWORD,
        tool_name="craft_item_tool",
        tool_input={"recipe": "sword"},
        state_effect="old_sword can be added to inventory on success.",
    ),
}


def serialize_craft_actions(phase: CraftPhase) -> AvailableActions:
    """Return user-facing craft actions available in the current phase."""
    return serialize_actions(
        CRAFT_TRANSITIONS,
        phase,
        metadata_by_event=tool_action_metadata(CRAFT_TOOL_BINDINGS),
    )


def resolve_craft_transition(
    phase: CraftPhase,
    event: CraftEvent,
) -> CraftTransitionRule | None:
    """Find the craft transition rule for the given phase and event."""
    return resolve_transition(CRAFT_TRANSITIONS, phase, event)


def answer_craft_result_question(
    *,
    phase: CraftPhase,
    latest_result: LatestCraftResult | None,
    user_input: str,
) -> str | None:
    """Answer a follow-up question about the latest craft result when possible."""
    if phase != CraftPhase.RESULT or latest_result is None:
        return None

    normalized_text = user_input.lower()
    if not any(keyword in normalized_text for keyword in ("어떤", "뭐", "what")):
        return None

    item_name = latest_result.get("item_name", "알 수 없는 아이템")
    recipe = latest_result.get("recipe", "아이템")
    return f"방금 제작한 {recipe}은 {item_name}입니다."
