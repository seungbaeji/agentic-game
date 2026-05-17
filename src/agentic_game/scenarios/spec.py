"""Common scenario model shared by all game scenarios."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from agentic_game.flow.models import TransitionRule


class ScenarioNode(StrEnum):
    DECISION = "decision"
    FLOW = "flow"
    HITL = "hitl"
    EXECUTE = "execute"
    RESPONSE = "response"
    ASK_USER = "ask_user"


@dataclass(frozen=True)
class ScenarioSpec[PhaseT, EventT]:
    name: str
    initial_phase: PhaseT
    transitions: Sequence[TransitionRule[PhaseT, EventT]]
    phase_to_node: Mapping[PhaseT, ScenarioNode]
