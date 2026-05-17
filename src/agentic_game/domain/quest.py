from __future__ import annotations

from enum import StrEnum


class QuestPhase(StrEnum):
    AVAILABLE = "available"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    TURN_IN = "turn_in"
    COMPLETE = "complete"
    FAILED = "failed"


class QuestEvent(StrEnum):
    ACCEPT = "accept"
    START = "start"
    PROGRESS = "progress"
    TURN_IN = "turn_in"
    COMPLETE = "complete"
    ABANDON = "abandon"
    FAIL = "fail"
