from __future__ import annotations

from agentic_game.domain.skill_training import (
    SkillTrainingEvent,
    SkillTrainingPhase,
)
from agentic_game.flow.models import AvailableActions, TransitionRule
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type SkillTrainingTransitionRule = TransitionRule[
    SkillTrainingPhase,
    SkillTrainingEvent,
]


SKILL_TRAINING_TRANSITIONS: list[SkillTrainingTransitionRule] = [
    TransitionRule(
        SkillTrainingPhase.SELECT_SKILL,
        SkillTrainingEvent.SELECT_SWORDSMANSHIP,
        SkillTrainingPhase.TRAIN,
        "검술 선택",
        "검술 훈련을 선택합니다.",
    ),
    TransitionRule(
        SkillTrainingPhase.SELECT_SKILL,
        SkillTrainingEvent.SELECT_ALCHEMY,
        SkillTrainingPhase.TRAIN,
        "연금술 선택",
        "연금술 훈련을 선택합니다.",
    ),
    TransitionRule(
        SkillTrainingPhase.TRAIN,
        SkillTrainingEvent.PRACTICE,
        SkillTrainingPhase.RESOLVE,
        "훈련 실행",
        "선택한 스킬 훈련을 실행합니다.",
    ),
    TransitionRule(
        SkillTrainingPhase.RESOLVE,
        SkillTrainingEvent.RETRY,
        SkillTrainingPhase.TRAIN,
        "다시 훈련",
        "결과를 보고 같은 스킬을 다시 훈련합니다.",
    ),
    TransitionRule(
        SkillTrainingPhase.RESOLVE,
        SkillTrainingEvent.LEVEL_UP,
        SkillTrainingPhase.LEVEL_UP,
        "레벨 상승",
        "충분한 성과를 얻어 스킬 레벨을 올립니다.",
    ),
    TransitionRule(
        SkillTrainingPhase.LEVEL_UP,
        SkillTrainingEvent.COMPLETE,
        SkillTrainingPhase.COMPLETE,
        "훈련 완료",
        "성장 결과를 저장하고 훈련을 마칩니다.",
    ),
]


def serialize_skill_training_actions(
    phase: SkillTrainingPhase,
) -> AvailableActions:
    """Return user-facing skill training actions available in the current phase."""
    return serialize_actions(SKILL_TRAINING_TRANSITIONS, phase)


def resolve_skill_training_transition(
    phase: SkillTrainingPhase,
    event: SkillTrainingEvent,
) -> SkillTrainingTransitionRule | None:
    """Find the skill training transition rule for the given phase and event."""
    return resolve_transition(SKILL_TRAINING_TRANSITIONS, phase, event)
