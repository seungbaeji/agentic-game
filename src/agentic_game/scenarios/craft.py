from __future__ import annotations

from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.flow.craft import serialize_craft_actions


def infer_craft_event(phase: CraftPhase, user_text: str) -> CraftEvent | None:
    """Infer a craft event from explicit recipe keywords."""
    available_events = {action["event"] for action in serialize_craft_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        CraftEvent.CRAFT_POTION: ("potion", "포션", "회복 물약"),
        CraftEvent.CRAFT_SWORD: ("sword", "검", "칼"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
