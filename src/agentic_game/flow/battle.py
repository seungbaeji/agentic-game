from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.flow.models import ActionCard, AvailableActions, TransitionRule
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type BattleTransitionRule = TransitionRule[BattlePhase, BattleEvent]


BATTLE_TRANSITIONS: list[BattleTransitionRule] = [
    TransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.CONTINUE,
        BattlePhase.ACTION,
        "전투 시작",
        "전투 행동 선택 단계로 이동합니다.",
    ),
    TransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.ATTACK,
        BattlePhase.RESOLVE,
        "전투 시작 후 공격",
        "전투를 시작하고 곧바로 적을 공격합니다.",
    ),
    TransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.DEFEND,
        BattlePhase.RESOLVE,
        "전투 시작 후 방어",
        "전투를 시작하고 곧바로 방어 자세를 취합니다.",
    ),
    TransitionRule(
        BattlePhase.PREPARE,
        BattleEvent.FLEE,
        BattlePhase.RESOLVE,
        "전투 시작 후 도망",
        "전투를 시작하고 곧바로 도망을 시도합니다.",
    ),
    TransitionRule(
        BattlePhase.ACTION,
        BattleEvent.ATTACK,
        BattlePhase.RESOLVE,
        "공격",
        "무기를 사용해 적을 공격합니다.",
    ),
    TransitionRule(
        BattlePhase.ACTION,
        BattleEvent.DEFEND,
        BattlePhase.RESOLVE,
        "방어",
        "방어 자세를 취해 피해를 줄입니다.",
    ),
    TransitionRule(
        BattlePhase.ACTION,
        BattleEvent.FLEE,
        BattlePhase.RESOLVE,
        "도망",
        "전투에서 도망을 시도합니다.",
    ),
    TransitionRule(
        BattlePhase.RESOLVE,
        BattleEvent.RETRY,
        BattlePhase.ACTION,
        "다시 행동 선택",
        "이전 결과를 보고 다시 행동을 선택합니다.",
    ),
    TransitionRule(
        BattlePhase.RESOLVE,
        BattleEvent.COMPLETE,
        BattlePhase.COMPLETE,
        "전투 종료",
        "현재 전투를 종료합니다.",
    ),
]

BATTLE_ACTION_METADATA: dict[BattleEvent, ActionCard] = {
    BattleEvent.ATTACK: {
        "tool_name": "resolve_battle_tool",
        "state_effect": "player EXP can increase when the attack hits.",
        "risk": "state_change",
    },
    BattleEvent.DEFEND: {
        "tool_name": "resolve_battle_tool",
        "state_effect": "player HP can decrease if guard breaks.",
        "risk": "state_change",
    },
    BattleEvent.FLEE: {
        "tool_name": "resolve_battle_tool",
        "state_effect": "player HP can decrease if fleeing fails.",
        "risk": "state_change",
    },
}


def serialize_battle_actions(phase: BattlePhase) -> AvailableActions:
    """Return user-facing battle actions available in the current phase."""
    return serialize_actions(
        BATTLE_TRANSITIONS,
        phase,
        metadata_by_event=BATTLE_ACTION_METADATA,
    )


def resolve_battle_transition(
    phase: BattlePhase,
    event: BattleEvent,
) -> BattleTransitionRule | None:
    """Find the battle transition rule for the given phase and event."""
    return resolve_transition(BATTLE_TRANSITIONS, phase, event)
