from __future__ import annotations

from collections.abc import Mapping, Sequence

from agentic_game.flow.models import ActionCard, AvailableActions, TransitionRule


def serialize_actions[PhaseT, EventT](
    transitions: Sequence[TransitionRule[PhaseT, EventT]],
    phase: PhaseT,
    *,
    metadata_by_event: Mapping[EventT, ActionCard] | None = None,
) -> AvailableActions:
    """Return user-facing actions available in the current phase."""
    actions: AvailableActions = []
    for rule in transitions:
        if rule.from_phase != phase:
            continue

        action: ActionCard = {
            "event": rule.on_event.value,
            "label": rule.label,
            "description": rule.description,
        }
        if metadata_by_event is not None:
            action.update(metadata_by_event.get(rule.on_event, {}))
        actions.append(action)

    return actions


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
