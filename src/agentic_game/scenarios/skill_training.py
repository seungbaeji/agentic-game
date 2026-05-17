"""Skill-training-specific user intent rules."""

from __future__ import annotations

from agentic_game.domain.skill_training import SkillTrainingEvent, SkillTrainingPhase
from agentic_game.flow.skill_training import serialize_skill_training_actions


def infer_skill_training_event(
    phase: SkillTrainingPhase,
    user_text: str,
) -> SkillTrainingEvent | None:
    """Infer a skill training event from explicit training keywords."""
    available_events = {
        action["event"] for action in serialize_skill_training_actions(phase)
    }
    normalized_text = user_text.lower()
    event_by_keywords = {
        SkillTrainingEvent.SELECT_SWORDSMANSHIP: ("sword", "검술"),
        SkillTrainingEvent.SELECT_ALCHEMY: ("alchemy", "연금술"),
        SkillTrainingEvent.PRACTICE: ("practice", "train", "훈련", "연습"),
        SkillTrainingEvent.RETRY: ("retry", "다시"),
        SkillTrainingEvent.LEVEL_UP: ("level", "레벨", "성장"),
        SkillTrainingEvent.COMPLETE: ("complete", "완료", "마칠"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
