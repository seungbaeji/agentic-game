from __future__ import annotations

from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.trade import serialize_trade_actions


def infer_trade_event(phase: TradePhase, user_text: str) -> TradeEvent | None:
    """Infer a trade event from explicit commerce keywords."""
    available_events = {action["event"] for action in serialize_trade_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        TradeEvent.SELECT_ITEM: ("select", "item", "아이템", "고를", "선택"),
        TradeEvent.OFFER: ("offer", "price", "제안", "가격", "흥정"),
        TradeEvent.ACCEPT_PRICE: ("accept", "수락", "좋아", "구매"),
        TradeEvent.DECLINE_PRICE: ("decline", "거절", "비싸", "다시"),
        TradeEvent.CONFIRM: ("confirm", "확정", "교환", "완료"),
        TradeEvent.CANCEL: ("cancel", "취소", "그만"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
