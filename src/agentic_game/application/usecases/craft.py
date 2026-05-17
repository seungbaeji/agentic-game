from __future__ import annotations

from dataclasses import dataclass

from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.ports import RandomPort
from agentic_game.domain.craft import CraftResult, craft_result
from agentic_game.domain.game_state import InventoryState


@dataclass(frozen=True, slots=True)
class InventoryDelta:
    item_id: str
    quantity: int


@dataclass(frozen=True, slots=True)
class CraftItemResult:
    craft: CraftResult
    inventory_delta: InventoryDelta | None = None
    inventory: InventoryState | None = None

    @property
    def recipe(self) -> str:
        return self.craft.recipe

    @property
    def item_name(self) -> str:
        return self.craft.item_name

    @property
    def dice(self) -> int:
        return self.craft.dice

    @property
    def success(self) -> bool:
        return self.craft.success

    @property
    def bonus(self) -> bool:
        return self.craft.bonus


def craft_item(
    recipe: str,
    *,
    random: RandomPort,
) -> CraftItemResult:
    """Run the craft item use case with injected randomness."""
    result = craft_result(recipe=recipe, dice=random.roll_d20())
    return CraftItemResult(craft=result)


def craft_item_and_store_reward(
    recipe: str,
    *,
    random: RandomPort,
    game_state: GameStateRepository,
) -> CraftItemResult:
    """Run crafting and persist the crafted item when the attempt succeeds."""
    result = craft_result(recipe=recipe, dice=random.roll_d20())
    if not result.success:
        return CraftItemResult(craft=result)

    delta = InventoryDelta(item_id=result.item_name, quantity=1)
    inventory = game_state.add_item(
        item_id=delta.item_id,
        quantity=delta.quantity,
    )
    return CraftItemResult(
        craft=result,
        inventory_delta=delta,
        inventory=inventory,
    )
