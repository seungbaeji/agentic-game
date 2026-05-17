from __future__ import annotations

from typing import Any

from agentic_game.domain.craft import (
    CRAFT_POLICIES,
    CraftCategory,
    CraftEvent,
    CraftPhase,
    craft_event_to_category,
)
from agentic_game.flow.models import (
    AvailableActions,
    ToolBinding,
    TransitionRule,
    tool_action_metadata,
)
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type LatestCraftResult = dict[str, Any]


type CraftTransitionRule = TransitionRule[CraftPhase, CraftEvent]


CRAFT_CATEGORY_EVENTS: tuple[CraftEvent, ...] = (
    CraftEvent.CRAFT_CONSUMABLE,
    CraftEvent.CRAFT_WEAPON,
    CraftEvent.CRAFT_ARMOR,
    CraftEvent.CRAFT_ACCESSORY,
    CraftEvent.CRAFT_TOOL,
    CraftEvent.CRAFT_MATERIAL,
)


def _category_label(event: CraftEvent) -> str:
    category = craft_event_to_category(event)
    return _category_name(category.value if category is not None else None)


def _category_name(category: str | None) -> str:
    if category == CraftCategory.CONSUMABLE:
        return "소모품"
    if category == CraftCategory.WEAPON:
        return "무기"
    if category == CraftCategory.ARMOR:
        return "방어구"
    if category == CraftCategory.ACCESSORY:
        return "장신구"
    if category == CraftCategory.TOOL:
        return "도구"
    if category == CraftCategory.MATERIAL:
        return "재료"
    return "아이템"


CRAFT_TRANSITIONS: list[CraftTransitionRule] = [
    TransitionRule(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CONTINUE,
        CraftPhase.CRAFT,
        "제작 단계로 이동",
        "제작할 아이템의 범주와 상세 내용을 정합니다.",
    ),
    *[
        TransitionRule(
            CraftPhase.SELECT_RECIPE,
            event,
            CraftPhase.RESULT,
            f"{_category_label(event)} 제작",
            f"{_category_label(event)} 범주의 아이템 제작을 시도합니다.",
        )
        for event in CRAFT_CATEGORY_EVENTS
    ],
    *[
        TransitionRule(
            CraftPhase.CRAFT,
            event,
            CraftPhase.RESULT,
            f"{_category_label(event)} 제작",
            f"{_category_label(event)} 범주의 아이템 제작을 시도합니다.",
        )
        for event in CRAFT_CATEGORY_EVENTS
    ],
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
    event: ToolBinding(
        event=event,
        tool_name="craft_item_tool",
        tool_input={"category": craft_event_to_category(event).value},
        state_effect=CRAFT_POLICIES[craft_event_to_category(event)].state_effect,
    )
    for event in CRAFT_CATEGORY_EVENTS
    if craft_event_to_category(event) is not None
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

    display_name = latest_result.get("display_name") or latest_result.get(
        "item_name",
        "알 수 없는 아이템",
    )
    category = _category_name(latest_result.get("category"))
    effect = latest_result.get("requested_effect")
    if effect:
        return f"방금 제작한 {display_name}은 {category} 범주의 아이템이고, 의도한 효과는 {effect}입니다."

    return f"방금 제작한 {display_name}은 {category} 범주의 아이템입니다."
