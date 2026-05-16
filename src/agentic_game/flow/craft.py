from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.flow.models import AvailableActions

type LatestCraftResult = dict[str, Any]


@dataclass(frozen=True)
class CraftTransitionRule:
    from_phase: CraftPhase
    on_event: CraftEvent
    to_phase: CraftPhase
    label: str
    description: str


CRAFT_TRANSITIONS: list[CraftTransitionRule] = [
    CraftTransitionRule(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CONTINUE,
        CraftPhase.CRAFT,
        "제작 단계로 이동",
        "제작할 아이템을 선택합니다.",
    ),
    CraftTransitionRule(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CRAFT_POTION,
        CraftPhase.RESULT,
        "포션 제작",
        "제작을 시작하고 곧바로 회복 포션 제작을 시도합니다.",
    ),
    CraftTransitionRule(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CRAFT_SWORD,
        CraftPhase.RESULT,
        "검 제작",
        "제작을 시작하고 곧바로 낡은 검 제작을 시도합니다.",
    ),
    CraftTransitionRule(
        CraftPhase.CRAFT,
        CraftEvent.CRAFT_POTION,
        CraftPhase.RESULT,
        "포션 제작",
        "회복 포션 제작을 시도합니다.",
    ),
    CraftTransitionRule(
        CraftPhase.CRAFT,
        CraftEvent.CRAFT_SWORD,
        CraftPhase.RESULT,
        "검 제작",
        "낡은 검 제작을 시도합니다.",
    ),
    CraftTransitionRule(
        CraftPhase.RESULT,
        CraftEvent.RETRY,
        CraftPhase.CRAFT,
        "다시 제작",
        "제작 결과를 보고 다시 제작합니다.",
    ),
    CraftTransitionRule(
        CraftPhase.RESULT,
        CraftEvent.COMPLETE,
        CraftPhase.COMPLETE,
        "제작 종료",
        "제작 업무를 종료합니다.",
    ),
]


def serialize_craft_actions(phase: CraftPhase) -> AvailableActions:
    """Return user-facing craft actions available in the current phase."""
    return [
        {
            "event": rule.on_event.value,
            "label": rule.label,
            "description": rule.description,
        }
        for rule in CRAFT_TRANSITIONS
        if rule.from_phase == phase
    ]


def resolve_craft_transition(
    phase: CraftPhase,
    event: CraftEvent,
) -> CraftTransitionRule | None:
    """Find the craft transition rule for the given phase and event."""
    for rule in CRAFT_TRANSITIONS:
        if rule.from_phase == phase and rule.on_event == event:
            return rule
    return None


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
