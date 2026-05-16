from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


class SubgraphName(StrEnum):
    BATTLE = "battle"
    CRAFT = "craft"


class ActionSpec(TypedDict):
    event: str
    label: str
    description: str


type AvailableActions = list[ActionSpec]
