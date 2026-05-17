"""Battle-specific user intent rules."""

from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.flow.battle import serialize_battle_actions


def infer_battle_event(phase: BattlePhase, user_text: str) -> BattleEvent | None:
    """Infer a battle event from explicit user action keywords."""
    available_events = {action["event"] for action in serialize_battle_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        BattleEvent.ATTACK: ("attack", "공격"),
        BattleEvent.DEFEND: ("defend", "방어"),
        BattleEvent.FLEE: ("flee", "도망", "회피"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
