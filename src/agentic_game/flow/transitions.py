from __future__ import annotations

from collections.abc import Sequence

from agentic_game.flow.models import AvailableActions, TransitionRule


def serialize_actions[PhaseT, EventT](
    transitions: Sequence[TransitionRule[PhaseT, EventT]],
    phase: PhaseT,
) -> AvailableActions:
    """Return user-facing actions available in the current phase."""
    return [
        {
            "event": rule.on_event.value,
            "label": rule.label,
            "description": rule.description,
        }
        for rule in transitions
        if rule.from_phase == phase
    ]


def resolve_transition[PhaseT, EventT](
    transitions: Sequence[TransitionRule[PhaseT, EventT]],
    phase: PhaseT,
    event: EventT,
) -> TransitionRule[PhaseT, EventT] | None:
    """Find the transition rule for the given phase and event."""
    for rule in transitions:
        if rule.from_phase == phase and rule.on_event == event:
            return rule
    return None
