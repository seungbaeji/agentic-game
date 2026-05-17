from __future__ import annotations

from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.flow.models import AvailableActions, TransitionRule
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type QuestTransitionRule = TransitionRule[QuestPhase, QuestEvent]


QUEST_TRANSITIONS: list[QuestTransitionRule] = [
    TransitionRule(
        QuestPhase.AVAILABLE,
        QuestEvent.ACCEPT,
        QuestPhase.ACCEPTED,
        "퀘스트 수락",
        "새 퀘스트를 수락합니다.",
    ),
    TransitionRule(
        QuestPhase.ACCEPTED,
        QuestEvent.START,
        QuestPhase.IN_PROGRESS,
        "퀘스트 시작",
        "퀘스트 목표 수행을 시작합니다.",
    ),
    TransitionRule(
        QuestPhase.IN_PROGRESS,
        QuestEvent.PROGRESS,
        QuestPhase.TURN_IN,
        "목표 달성",
        "목표를 달성하고 보고 단계로 이동합니다.",
    ),
    TransitionRule(
        QuestPhase.IN_PROGRESS,
        QuestEvent.ABANDON,
        QuestPhase.FAILED,
        "퀘스트 포기",
        "진행 중인 퀘스트를 포기합니다.",
    ),
    TransitionRule(
        QuestPhase.IN_PROGRESS,
        QuestEvent.FAIL,
        QuestPhase.FAILED,
        "퀘스트 실패",
        "조건을 만족하지 못해 퀘스트에 실패합니다.",
    ),
    TransitionRule(
        QuestPhase.TURN_IN,
        QuestEvent.COMPLETE,
        QuestPhase.COMPLETE,
        "퀘스트 완료",
        "보상을 받고 퀘스트를 완료합니다.",
    ),
]


def serialize_quest_actions(phase: QuestPhase) -> AvailableActions:
    """Return user-facing quest actions available in the current phase."""
    return serialize_actions(QUEST_TRANSITIONS, phase)


def resolve_quest_transition(
    phase: QuestPhase,
    event: QuestEvent,
) -> QuestTransitionRule | None:
    """Find the quest transition rule for the given phase and event."""
    return resolve_transition(QUEST_TRANSITIONS, phase, event)
