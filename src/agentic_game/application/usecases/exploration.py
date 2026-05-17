from __future__ import annotations

from dataclasses import dataclass

from agentic_game.application.game_state import GameStateRepository
from agentic_game.domain.exploration import ExplorationEvent
from agentic_game.domain.game_state import WorldState


@dataclass(frozen=True, slots=True)
class ExplorationResult:
    location_id: str
    world: WorldState


def location_id_from_event(event: ExplorationEvent | None) -> str:
    """Return the world location id for an exploration event."""
    if event == ExplorationEvent.TAKE_RUINS:
        return "old_ruins"
    if event == ExplorationEvent.INSPECT:
        return "hidden_trail"
    return "forest_path"


def discover_exploration_location(
    *,
    event: ExplorationEvent | None,
    game_state: GameStateRepository,
) -> ExplorationResult:
    """Persist the location discovered by exploration."""
    location_id = location_id_from_event(event)
    world = game_state.discover_location(location_id=location_id)
    return ExplorationResult(location_id=location_id, world=world)
