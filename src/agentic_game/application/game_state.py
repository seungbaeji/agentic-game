from __future__ import annotations

from agentic_game.application.ports import StorePort
from agentic_game.domain.game_state import (
    InventoryState,
    SkillBook,
    add_inventory_item,
    add_skill_exp,
    level_up_skill,
)

INVENTORY_NAMESPACE = ("game", "inventory")
INVENTORY_KEY = "latest"
SKILLS_NAMESPACE = ("game", "skills")
SKILLS_KEY = "latest"


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

    def load_skills(self) -> SkillBook:
        """Load player skills, returning an empty skill book when none exists."""
        try:
            value = self._store.get(
                namespace=SKILLS_NAMESPACE,
                key=SKILLS_KEY,
            )
        except KeyError:
            return SkillBook()

        if isinstance(value, SkillBook):
            return value

        return SkillBook()

    def save_skills(self, skill_book: SkillBook) -> str:
        """Persist player skills and return its store reference."""
        return self._store.put(
            namespace=SKILLS_NAMESPACE,
            key=SKILLS_KEY,
            value=skill_book,
        )

    def add_skill_exp(self, *, skill_id: str, exp: int) -> SkillBook:
        """Add exp to a stored skill and persist the updated skill book."""
        skill_book = add_skill_exp(
            self.load_skills(),
            skill_id=skill_id,
            exp=exp,
        )
        self.save_skills(skill_book)
        return skill_book

    def level_up_skill(self, *, skill_id: str) -> SkillBook:
        """Increase a stored skill level and persist the updated skill book."""
        skill_book = level_up_skill(
            self.load_skills(),
            skill_id=skill_id,
        )
        self.save_skills(skill_book)
        return skill_book
