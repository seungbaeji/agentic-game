from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypedDict


class SubgraphName(StrEnum):
    BATTLE = "battle"
    CRAFT = "craft"
    EXPLORATION = "exploration"
    TRADE = "trade"
    QUEST = "quest"
    DIALOGUE = "dialogue"
    SKILL_TRAINING = "skill_training"


class ActionCard(TypedDict, total=False):
    event: str
    label: str
    description: str
    tool_name: str
    state_effect: str
    risk: Literal["none", "read", "state_change"]


type AvailableActions = list[ActionCard]


@dataclass(frozen=True)
class TransitionRule[PhaseT, EventT]:
    from_phase: PhaseT
    on_event: EventT
    to_phase: PhaseT
    label: str
    description: str


@dataclass(frozen=True)
class ToolBinding[EventT]:
    event: EventT
    tool_name: str
    tool_input: Mapping[str, object]
    state_effect: str
    risk: Literal["none", "read", "state_change"] = "state_change"


def tool_action_metadata[EventT](
    bindings: Mapping[EventT, ToolBinding[EventT]],
) -> dict[EventT, ActionCard]:
    """Return user-facing action metadata from executable tool bindings."""
    return {
        event: {
            "tool_name": binding.tool_name,
            "state_effect": binding.state_effect,
            "risk": binding.risk,
        }
        for event, binding in bindings.items()
    }
