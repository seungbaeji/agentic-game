from __future__ import annotations

from agentic_game.application.ports import StorePort
from agentic_game.domain.game_state import (
    InventoryState,
    add_inventory_item,
)

INVENTORY_NAMESPACE = ("game", "inventory")
INVENTORY_KEY = "latest"


class GameStateRepository:
    def __init__(self, store: StorePort) -> None:
        self._store = store

    def load_inventory(self) -> InventoryState:
        """Load player inventory, returning an empty inventory when none exists."""
        try:
            value = self._store.get(
                namespace=INVENTORY_NAMESPACE,
                key=INVENTORY_KEY,
            )
        except KeyError:
            return InventoryState()

        if isinstance(value, InventoryState):
            return value

        return InventoryState()

    def save_inventory(self, inventory: InventoryState) -> str:
        """Persist player inventory and return its store reference."""
        return self._store.put(
            namespace=INVENTORY_NAMESPACE,
            key=INVENTORY_KEY,
            value=inventory,
        )

    def add_item(self, *, item_id: str, quantity: int = 1) -> InventoryState:
        """Add an item to the stored inventory and persist the updated state."""
        inventory = add_inventory_item(
            self.load_inventory(),
            item_id=item_id,
            quantity=quantity,
        )
        self.save_inventory(inventory)
        return inventory
