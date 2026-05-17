"""Quest-specific user intent rules."""

from __future__ import annotations

from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.flow.quest import serialize_quest_actions


def infer_quest_event(phase: QuestPhase, user_text: str) -> QuestEvent | None:
    """Infer a quest event from explicit quest progress keywords."""
    available_events = {action["event"] for action in serialize_quest_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        QuestEvent.ACCEPT: ("accept", "수락", "받을"),
        QuestEvent.START: ("start", "시작", "출발"),
        QuestEvent.PROGRESS: ("progress", "진행", "달성", "목표"),
        QuestEvent.COMPLETE: ("complete", "완료", "보고", "보상"),
        QuestEvent.ABANDON: ("abandon", "포기", "그만"),
        QuestEvent.FAIL: ("fail", "실패"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
