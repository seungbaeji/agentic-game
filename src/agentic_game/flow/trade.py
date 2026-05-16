from __future__ import annotations

from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.models import AvailableActions, TransitionRule
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type TradeTransitionRule = TransitionRule[TradePhase, TradeEvent]


TRADE_TRANSITIONS: list[TradeTransitionRule] = [
    TransitionRule(
        TradePhase.BROWSE,
        TradeEvent.SELECT_ITEM,
        TradePhase.NEGOTIATE,
        "아이템 선택",
        "거래할 아이템을 선택하고 가격 협상으로 이동합니다.",
    ),
    TransitionRule(
        TradePhase.NEGOTIATE,
        TradeEvent.OFFER,
        TradePhase.CONFIRM,
        "가격 제안",
        "제안한 가격을 확인합니다.",
    ),
    TransitionRule(
        TradePhase.NEGOTIATE,
        TradeEvent.CANCEL,
        TradePhase.CANCELLED,
        "거래 취소",
        "협상을 중단합니다.",
    ),
    TransitionRule(
        TradePhase.CONFIRM,
        TradeEvent.ACCEPT_PRICE,
        TradePhase.EXCHANGE,
        "가격 수락",
        "가격을 수락하고 교환을 진행합니다.",
    ),
    TransitionRule(
        TradePhase.CONFIRM,
        TradeEvent.DECLINE_PRICE,
        TradePhase.NEGOTIATE,
        "가격 거절",
        "가격을 거절하고 다시 협상합니다.",
    ),
    TransitionRule(
        TradePhase.CONFIRM,
        TradeEvent.CANCEL,
        TradePhase.CANCELLED,
        "거래 취소",
        "거래를 취소합니다.",
    ),
    TransitionRule(
        TradePhase.EXCHANGE,
        TradeEvent.CONFIRM,
        TradePhase.COMPLETE,
        "교환 확정",
        "아이템과 재화를 교환하고 거래를 마칩니다.",
    ),
]


def serialize_trade_actions(phase: TradePhase) -> AvailableActions:
    """Return user-facing trade actions available in the current phase."""
    return serialize_actions(TRADE_TRANSITIONS, phase)


def resolve_trade_transition(
    phase: TradePhase,
    event: TradeEvent,
) -> TradeTransitionRule | None:
    """Find the trade transition rule for the given phase and event."""
    return resolve_transition(TRADE_TRANSITIONS, phase, event)
