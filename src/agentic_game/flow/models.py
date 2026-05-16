from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict


class SubgraphName(StrEnum):
    BATTLE = "battle"
    CRAFT = "craft"
    EXPLORATION = "exploration"
    TRADE = "trade"


class ActionSpec(TypedDict):
    event: str
    label: str
    description: str


type AvailableActions = list[ActionSpec]


@dataclass(frozen=True)
class TransitionRule[PhaseT, EventT]:
    from_phase: PhaseT
    on_event: EventT
    to_phase: PhaseT
    label: str
    description: str
