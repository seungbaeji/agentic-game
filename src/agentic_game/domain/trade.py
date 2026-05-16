from __future__ import annotations

from enum import StrEnum


class TradePhase(StrEnum):
    BROWSE = "browse"
    NEGOTIATE = "negotiate"
    CONFIRM = "confirm"
    EXCHANGE = "exchange"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class TradeEvent(StrEnum):
    SELECT_ITEM = "select_item"
    OFFER = "offer"
    ACCEPT_PRICE = "accept_price"
    DECLINE_PRICE = "decline_price"
    CONFIRM = "confirm"
    CANCEL = "cancel"
