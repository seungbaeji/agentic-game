from __future__ import annotations

from agentic_game.application.ports import RandomPort
from agentic_game.domain.battle import BattleAction, BattleResult, resolve_battle_result


def resolve_battle_action(
    action: str,
    *,
    random: RandomPort,
) -> BattleResult:
    """Run the battle action use case with injected randomness."""
    dice = random.roll_d20()
    if action == BattleAction.ATTACK:
        damage = random.roll_damage(5, 15)
    elif action == BattleAction.DEFEND:
        damage = random.roll_damage(1, 5)
    elif action == BattleAction.FLEE:
        damage = random.roll_damage(3, 8)
    else:
        damage = 0
    return resolve_battle_result(action=action, dice=dice, damage=damage)
