"""Dialogue-specific user intent rules."""

from __future__ import annotations

from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.flow.dialogue import serialize_dialogue_actions


def infer_dialogue_event(
    phase: DialoguePhase,
    user_text: str,
) -> DialogueEvent | None:
    """Infer a dialogue event from explicit NPC conversation keywords."""
    available_events = {action["event"] for action in serialize_dialogue_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        DialogueEvent.ASK_RUMOR: ("rumor", "소문"),
        DialogueEvent.ASK_TRADE: ("trade", "거래"),
        DialogueEvent.THANK: ("thank", "감사", "고마"),
        DialogueEvent.LEAVE: ("leave", "떠날", "종료", "그만"),
        DialogueEvent.CLAIM_REWARD: ("reward", "보상", "받을"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
