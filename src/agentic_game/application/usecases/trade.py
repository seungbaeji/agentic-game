from __future__ import annotations

from dataclasses import dataclass

from agentic_game.application.game_state import GameStateRepository
from agentic_game.domain.game_state import InventoryState, PlayerState

DEFAULT_TRADE_ITEM_ID = "travel_ration"
DEFAULT_TRADE_PRICE = 15


@dataclass(frozen=True, slots=True)
class TradeResult:
    item_id: str
    price: int
    player: PlayerState
    inventory: InventoryState


def exchange_item(
    *,
    game_state: GameStateRepository,
    item_id: str = DEFAULT_TRADE_ITEM_ID,
    price: int = DEFAULT_TRADE_PRICE,
) -> TradeResult:
    """Persist a simple item purchase."""
    player = game_state.apply_player_delta(gold_change=-price)
    inventory = game_state.add_item(item_id=item_id, quantity=1)
    return TradeResult(
        item_id=item_id,
        price=price,
        player=player,
        inventory=inventory,
    )
