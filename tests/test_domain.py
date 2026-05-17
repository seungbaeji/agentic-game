from __future__ import annotations

import pytest

from agentic_game.domain.battle import BattleOutcome, resolve_battle_result
from agentic_game.domain.craft import CraftCategory, craft_result


@pytest.mark.parametrize(
    ("action", "dice", "damage", "outcome", "resolved_damage"),
    [
        ("attack", 18, 12, BattleOutcome.CRITICAL_HIT, 12),
        ("attack", 8, 7, BattleOutcome.HIT, 7),
        ("attack", 7, 9, BattleOutcome.MISS, 0),
        ("defend", 7, 4, BattleOutcome.BLOCKED, 0),
        ("defend", 6, 4, BattleOutcome.GUARD_BROKEN, 4),
        ("flee", 10, 5, BattleOutcome.ESCAPED, 0),
        ("flee", 9, 5, BattleOutcome.FAILED_TO_ESCAPE, 5),
        ("dance", 20, 99, BattleOutcome.INVALID_ACTION, 0),
    ],
)
def test_resolve_battle_result(
    action: str,
    dice: int,
    damage: int,
    outcome: BattleOutcome,
    resolved_damage: int,
) -> None:
    result = resolve_battle_result(action=action, dice=dice, damage=damage)

    assert result.action == action
    assert result.dice == dice
    assert result.outcome == outcome
    assert result.damage == resolved_damage


@pytest.mark.parametrize(
    ("category", "dice", "item_name", "display_name", "success", "bonus"),
    [
        (CraftCategory.CONSUMABLE, 7, "healing_potion", "회복 포션", True, False),
        (CraftCategory.CONSUMABLE, 6, "healing_potion", "회복 포션", False, False),
        (CraftCategory.WEAPON, 13, "old_sword", "낡은 검", True, False),
        (CraftCategory.WEAPON, 19, "old_sword", "낡은 검", True, True),
        (CraftCategory.TOOL, 10, "utility_tool", "도구", True, False),
    ],
)
def test_craft_result(
    category: CraftCategory,
    dice: int,
    item_name: str,
    display_name: str,
    success: bool,
    bonus: bool,
) -> None:
    result = craft_result(category=category, dice=dice)

    assert result.category == category
    assert result.item_name == item_name
    assert result.display_name == display_name
    assert result.dice == dice
    assert result.success is success
    assert result.bonus is bonus


def test_craft_result_preserves_llm_item_details() -> None:
    result = craft_result(
        category=CraftCategory.WEAPON,
        item_name="flame_dagger",
        display_name="불꽃 단검",
        requested_effect="burn",
        dice=13,
    )

    assert result.item_name == "flame_dagger"
    assert result.display_name == "불꽃 단검"
    assert result.requested_effect == "burn"
    assert result.success is True
