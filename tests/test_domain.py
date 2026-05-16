from __future__ import annotations

import pytest

from agentic_game.domain.battle import BattleOutcome, resolve_battle_result
from agentic_game.domain.craft import craft_result


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
    ("recipe", "dice", "item_name", "success", "bonus"),
    [
        ("potion", 7, "healing_potion", True, False),
        ("potion", 6, "healing_potion", False, False),
        ("sword", 13, "old_sword", True, False),
        ("sword", 19, "old_sword", True, True),
        ("unknown", 20, "unknown", False, False),
    ],
)
def test_craft_result(
    recipe: str,
    dice: int,
    item_name: str,
    success: bool,
    bonus: bool,
) -> None:
    result = craft_result(recipe=recipe, dice=dice)

    assert result.recipe == recipe
    assert result.item_name == item_name
    assert result.dice == dice
    assert result.success is success
    assert result.bonus is bonus
