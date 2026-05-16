from __future__ import annotations

from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.flow.models import AvailableActions, TransitionRule
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type ExplorationTransitionRule = TransitionRule[ExplorationPhase, ExplorationEvent]


EXPLORATION_TRANSITIONS: list[ExplorationTransitionRule] = [
    TransitionRule(
        ExplorationPhase.START,
        ExplorationEvent.CONTINUE,
        ExplorationPhase.CHOOSE_PATH,
        "탐험 시작",
        "갈림길로 이동합니다.",
    ),
    TransitionRule(
        ExplorationPhase.CHOOSE_PATH,
        ExplorationEvent.TAKE_FOREST,
        ExplorationPhase.ENCOUNTER,
        "숲길 선택",
        "숲길로 들어가 조우를 확인합니다.",
    ),
    TransitionRule(
        ExplorationPhase.CHOOSE_PATH,
        ExplorationEvent.TAKE_RUINS,
        ExplorationPhase.DISCOVER,
        "유적 선택",
        "유적으로 이동해 발견물을 조사합니다.",
    ),
    TransitionRule(
        ExplorationPhase.ENCOUNTER,
        ExplorationEvent.INSPECT,
        ExplorationPhase.DISCOVER,
        "조우 조사",
        "마주친 대상을 조사해 단서를 찾습니다.",
    ),
    TransitionRule(
        ExplorationPhase.ENCOUNTER,
        ExplorationEvent.RETREAT,
        ExplorationPhase.COMPLETE,
        "후퇴",
        "탐험을 중단하고 안전한 곳으로 돌아갑니다.",
    ),
    TransitionRule(
        ExplorationPhase.DISCOVER,
        ExplorationEvent.COMPLETE,
        ExplorationPhase.COMPLETE,
        "탐험 완료",
        "발견 내용을 정리하고 탐험을 마칩니다.",
    ),
]


def serialize_exploration_actions(phase: ExplorationPhase) -> AvailableActions:
    """Return user-facing exploration actions available in the current phase."""
    return serialize_actions(EXPLORATION_TRANSITIONS, phase)


def resolve_exploration_transition(
    phase: ExplorationPhase,
    event: ExplorationEvent,
) -> ExplorationTransitionRule | None:
    """Find the exploration transition rule for the given phase and event."""
    return resolve_transition(EXPLORATION_TRANSITIONS, phase, event)
