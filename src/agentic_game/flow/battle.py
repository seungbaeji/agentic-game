from __future__ import annotations

from dataclasses import dataclass

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.flow.models import AvailableActions


@dataclass(frozen=True)
class BattleTransitionRule:
    from_phase: BattlePhase
    on_event: BattleEvent
    to_phase: BattlePhase
    label: str
    description: str


BATTLE_TRANSITIONS: list[BattleTransitionRule] = [
    BattleTransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.CONTINUE,
        BattlePhase.ACTION,
        "전투 시작",
        "전투 행동 선택 단계로 이동합니다.",
    ),
    BattleTransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.ATTACK,
        BattlePhase.RESOLVE,
        "전투 시작 후 공격",
        "전투를 시작하고 곧바로 적을 공격합니다.",
    ),
    BattleTransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.DEFEND,
        BattlePhase.RESOLVE,
        "전투 시작 후 방어",
        "전투를 시작하고 곧바로 방어 자세를 취합니다.",
    ),
    BattleTransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.FLEE,
        BattlePhase.RESOLVE,
        "전투 시작 후 도망",
        "전투를 시작하고 곧바로 도망을 시도합니다.",
    ),
    BattleTransitionRule(
        BattlePhase.ACTION,
        BattleEvent.ATTACK,
        BattlePhase.RESOLVE,
        "공격",
        "무기를 사용해 적을 공격합니다.",
    ),
    BattleTransitionRule(
        BattlePhase.ACTION,
        BattleEvent.DEFEND,
        BattlePhase.RESOLVE,
        "방어",
        "방어 자세를 취해 피해를 줄입니다.",
    ),
    BattleTransitionRule(
        BattlePhase.ACTION,
        BattleEvent.FLEE,
        BattlePhase.RESOLVE,
        "도망",
        "전투에서 도망을 시도합니다.",
    ),
    BattleTransitionRule(
        BattlePhase.RESOLVE,
        BattleEvent.RETRY,
        BattlePhase.ACTION,
        "다시 행동 선택",
        "이전 결과를 보고 다시 행동을 선택합니다.",
    ),
    BattleTransitionRule(
        BattlePhase.RESOLVE,
        BattleEvent.COMPLETE,
        BattlePhase.COMPLETE,
        "전투 종료",
        "현재 전투를 종료합니다.",
    ),
]


def serialize_battle_actions(phase: BattlePhase) -> AvailableActions:
    """Return user-facing battle actions available in the current phase."""
    return [
        {
            "event": rule.on_event.value,
            "label": rule.label,
            "description": rule.description,
        }
        for rule in BATTLE_TRANSITIONS
        if rule.from_phase == phase
    ]


def resolve_battle_transition(
    phase: BattlePhase,
    event: BattleEvent,
) -> BattleTransitionRule | None:
    """Find the battle transition rule for the given phase and event."""
    for rule in BATTLE_TRANSITIONS:
        if rule.from_phase == phase and rule.on_event == event:
            return rule
    return None
