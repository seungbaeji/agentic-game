from __future__ import annotations

from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.flow.exploration import serialize_exploration_actions


def infer_exploration_event(
    phase: ExplorationPhase,
    user_text: str,
) -> ExplorationEvent | None:
    """Infer an exploration event from explicit path and action keywords."""
    available_events = {
        action["event"] for action in serialize_exploration_actions(phase)
    }
    normalized_text = user_text.lower()
    event_by_keywords = {
        ExplorationEvent.TAKE_FOREST: ("forest", "숲", "숲길"),
        ExplorationEvent.TAKE_RUINS: ("ruins", "유적"),
        ExplorationEvent.INSPECT: ("inspect", "조사", "살펴"),
        ExplorationEvent.RETREAT: ("retreat", "후퇴", "돌아"),
        ExplorationEvent.COMPLETE: ("complete", "완료", "마칠"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
