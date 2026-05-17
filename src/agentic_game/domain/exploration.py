from __future__ import annotations

from enum import StrEnum


class ExplorationPhase(StrEnum):
    START = "start"
    CHOOSE_PATH = "choose_path"
    ENCOUNTER = "encounter"
    DISCOVER = "discover"
    COMPLETE = "complete"


class ExplorationEvent(StrEnum):
    CONTINUE = "continue"
    TAKE_FOREST = "take_forest"
    TAKE_RUINS = "take_ruins"
    INSPECT = "inspect"
    RETREAT = "retreat"
    COMPLETE = "complete"
