from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CraftPhase(StrEnum):
    SELECT_RECIPE = "select_recipe"
    CRAFT = "craft"
    RESULT = "result"
    COMPLETE = "complete"


class CraftEvent(StrEnum):
    CONTINUE = "continue"
    CRAFT_POTION = "craft_potion"
    CRAFT_SWORD = "craft_sword"
    RETRY = "retry"
    COMPLETE = "complete"


class Recipe(StrEnum):
    POTION = "potion"
    SWORD = "sword"


@dataclass(frozen=True)
class CraftResult:
    recipe: str
    item_name: str
    dice: int
    success: bool
    bonus: bool


def craft_result(
    *,
    recipe: str,
    dice: int,
) -> CraftResult:
    """Resolve a crafting attempt into its deterministic domain result."""
    if recipe == Recipe.POTION:
        success_threshold = 7
        item_name = "healing_potion"
    elif recipe == Recipe.SWORD:
        success_threshold = 13
        item_name = "old_sword"
    else:
        success_threshold = 999
        item_name = "unknown"

    success = dice >= success_threshold
    bonus = success and dice >= 19

    return CraftResult(
        recipe=recipe,
        item_name=item_name,
        dice=dice,
        success=success,
        bonus=bonus,
    )
