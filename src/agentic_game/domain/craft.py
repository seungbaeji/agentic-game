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
    CRAFT_CONSUMABLE = "craft_consumable"
    CRAFT_WEAPON = "craft_weapon"
    CRAFT_ARMOR = "craft_armor"
    CRAFT_ACCESSORY = "craft_accessory"
    CRAFT_TOOL = "craft_tool"
    CRAFT_MATERIAL = "craft_material"
    RETRY = "retry"
    COMPLETE = "complete"


class CraftCategory(StrEnum):
    CONSUMABLE = "consumable"
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    TOOL = "tool"
    MATERIAL = "material"


@dataclass(frozen=True)
class CraftPolicy:
    success_threshold: int
    default_item_name: str
    default_display_name: str
    state_effect: str


@dataclass(frozen=True)
class CraftResult:
    category: str
    item_name: str
    display_name: str
    requested_effect: str | None
    dice: int
    success: bool
    bonus: bool


CRAFT_POLICIES: dict[CraftCategory, CraftPolicy] = {
    CraftCategory.CONSUMABLE: CraftPolicy(
        success_threshold=7,
        default_item_name="healing_potion",
        default_display_name="회복 포션",
        state_effect="consumable item can be added to inventory on success.",
    ),
    CraftCategory.WEAPON: CraftPolicy(
        success_threshold=13,
        default_item_name="old_sword",
        default_display_name="낡은 검",
        state_effect="weapon item can be added to inventory on success.",
    ),
    CraftCategory.ARMOR: CraftPolicy(
        success_threshold=12,
        default_item_name="reinforced_armor",
        default_display_name="강화 갑옷",
        state_effect="armor item can be added to inventory on success.",
    ),
    CraftCategory.ACCESSORY: CraftPolicy(
        success_threshold=15,
        default_item_name="minor_charm",
        default_display_name="작은 부적",
        state_effect="accessory item can be added to inventory on success.",
    ),
    CraftCategory.TOOL: CraftPolicy(
        success_threshold=10,
        default_item_name="utility_tool",
        default_display_name="도구",
        state_effect="tool item can be added to inventory on success.",
    ),
    CraftCategory.MATERIAL: CraftPolicy(
        success_threshold=6,
        default_item_name="refined_material",
        default_display_name="정제 재료",
        state_effect="material item can be added to inventory on success.",
    ),
}


def craft_event_to_category(event: CraftEvent) -> CraftCategory | None:
    """Return the craft category represented by a craft event."""
    return {
        CraftEvent.CRAFT_CONSUMABLE: CraftCategory.CONSUMABLE,
        CraftEvent.CRAFT_WEAPON: CraftCategory.WEAPON,
        CraftEvent.CRAFT_ARMOR: CraftCategory.ARMOR,
        CraftEvent.CRAFT_ACCESSORY: CraftCategory.ACCESSORY,
        CraftEvent.CRAFT_TOOL: CraftCategory.TOOL,
        CraftEvent.CRAFT_MATERIAL: CraftCategory.MATERIAL,
    }.get(event)


def craft_category_to_event(category: CraftCategory) -> CraftEvent:
    """Return the craft event represented by a craft category."""
    return {
        CraftCategory.CONSUMABLE: CraftEvent.CRAFT_CONSUMABLE,
        CraftCategory.WEAPON: CraftEvent.CRAFT_WEAPON,
        CraftCategory.ARMOR: CraftEvent.CRAFT_ARMOR,
        CraftCategory.ACCESSORY: CraftEvent.CRAFT_ACCESSORY,
        CraftCategory.TOOL: CraftEvent.CRAFT_TOOL,
        CraftCategory.MATERIAL: CraftEvent.CRAFT_MATERIAL,
    }[category]


def craft_result(
    *,
    category: str,
    item_name: str | None = None,
    display_name: str | None = None,
    requested_effect: str | None = None,
    dice: int,
) -> CraftResult:
    """Resolve a crafting attempt into its deterministic domain result."""
    craft_category = CraftCategory(category)
    policy = CRAFT_POLICIES[craft_category]

    success = dice >= policy.success_threshold
    bonus = success and dice >= 19

    return CraftResult(
        category=craft_category.value,
        item_name=item_name or policy.default_item_name,
        display_name=display_name or policy.default_display_name,
        requested_effect=requested_effect,
        dice=dice,
        success=success,
        bonus=bonus,
    )
