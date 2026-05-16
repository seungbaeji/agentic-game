from __future__ import annotations

from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.flow.models import AvailableActions, TransitionRule
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type DialogueTransitionRule = TransitionRule[DialoguePhase, DialogueEvent]


DIALOGUE_TRANSITIONS: list[DialogueTransitionRule] = [
    TransitionRule(
        DialoguePhase.GREETING,
        DialogueEvent.CONTINUE,
        DialoguePhase.CHOICE,
        "대화 시작",
        "NPC와 대화를 시작하고 선택지로 이동합니다.",
    ),
    TransitionRule(
        DialoguePhase.CHOICE,
        DialogueEvent.ASK_RUMOR,
        DialoguePhase.REACT,
        "소문 묻기",
        "NPC에게 주변 소문을 묻습니다.",
    ),
    TransitionRule(
        DialoguePhase.CHOICE,
        DialogueEvent.ASK_TRADE,
        DialoguePhase.REACT,
        "거래 묻기",
        "NPC에게 거래 가능 여부를 묻습니다.",
    ),
    TransitionRule(
        DialoguePhase.CHOICE,
        DialogueEvent.LEAVE,
        DialoguePhase.END,
        "대화 종료",
        "대화를 마칩니다.",
    ),
    TransitionRule(
        DialoguePhase.REACT,
        DialogueEvent.THANK,
        DialoguePhase.REWARD,
        "감사 인사",
        "NPC 반응에 감사하고 보상 여부를 확인합니다.",
    ),
    TransitionRule(
        DialoguePhase.REACT,
        DialogueEvent.LEAVE,
        DialoguePhase.END,
        "대화 종료",
        "보상 없이 대화를 마칩니다.",
    ),
    TransitionRule(
        DialoguePhase.REWARD,
        DialogueEvent.CLAIM_REWARD,
        DialoguePhase.END,
        "보상 수령",
        "보상을 받고 대화를 종료합니다.",
    ),
]


def serialize_dialogue_actions(phase: DialoguePhase) -> AvailableActions:
    """Return user-facing dialogue actions available in the current phase."""
    return serialize_actions(DIALOGUE_TRANSITIONS, phase)


def resolve_dialogue_transition(
    phase: DialoguePhase,
    event: DialogueEvent,
) -> DialogueTransitionRule | None:
    """Find the dialogue transition rule for the given phase and event."""
    return resolve_transition(DIALOGUE_TRANSITIONS, phase, event)
