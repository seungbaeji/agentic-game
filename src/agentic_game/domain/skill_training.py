from __future__ import annotations

from enum import StrEnum


class SkillTrainingPhase(StrEnum):
    SELECT_SKILL = "select_skill"
    TRAIN = "train"
    RESOLVE = "resolve"
    LEVEL_UP = "level_up"
    COMPLETE = "complete"


class SkillTrainingEvent(StrEnum):
    SELECT_SWORDSMANSHIP = "select_swordsmanship"
    SELECT_ALCHEMY = "select_alchemy"
    PRACTICE = "practice"
    RETRY = "retry"
    LEVEL_UP = "level_up"
    COMPLETE = "complete"
