from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InventoryItem:
    item_id: str
    quantity: int


@dataclass(frozen=True, slots=True)
class InventoryState:
    items: tuple[InventoryItem, ...] = ()


def add_inventory_item(
    inventory: InventoryState,
    *,
    item_id: str,
    quantity: int = 1,
) -> InventoryState:
    """Return inventory with quantity added for the given item."""
    if quantity <= 0:
        return inventory

    updated_items: list[InventoryItem] = []
    item_found = False

    for item in inventory.items:
        if item.item_id == item_id:
            updated_items.append(
                InventoryItem(
                    item_id=item.item_id,
                    quantity=item.quantity + quantity,
                )
            )
            item_found = True
        else:
            updated_items.append(item)

    if not item_found:
        updated_items.append(InventoryItem(item_id=item_id, quantity=quantity))

    return InventoryState(items=tuple(updated_items))
