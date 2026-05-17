from __future__ import annotations

from dataclasses import dataclass

from agentic_game.application.game_state import GameStateRepository
from agentic_game.domain.game_state import SkillBook
from agentic_game.domain.skill_training import SkillTrainingEvent

PRACTICE_EXP = 10


@dataclass(frozen=True, slots=True)
class SkillTrainingResult:
    skill_id: str
    skill_book: SkillBook


def skill_id_from_event(event: SkillTrainingEvent | None) -> str | None:
    """Return the selected skill id for a skill selection event."""
    if event == SkillTrainingEvent.SELECT_SWORDSMANSHIP:
        return "swordsmanship"
    if event == SkillTrainingEvent.SELECT_ALCHEMY:
        return "alchemy"
    return None


def practice_skill(
    *,
    skill_id: str,
    game_state: GameStateRepository,
) -> SkillTrainingResult:
    """Persist practice exp for a skill."""
    skill_book = game_state.add_skill_exp(
        skill_id=skill_id,
        exp=PRACTICE_EXP,
    )
    return SkillTrainingResult(skill_id=skill_id, skill_book=skill_book)


def level_up_trained_skill(
    *,
    skill_id: str,
    game_state: GameStateRepository,
) -> SkillTrainingResult:
    """Persist a level-up for a skill."""
    skill_book = game_state.level_up_skill(skill_id=skill_id)
    return SkillTrainingResult(skill_id=skill_id, skill_book=skill_book)
