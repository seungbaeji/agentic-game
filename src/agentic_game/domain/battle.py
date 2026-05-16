from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BattlePhase(StrEnum):
    PREPARE = "prepare"
    ACTION = "action"
    RESOLVE = "resolve"
    COMPLETE = "complete"


class BattleEvent(StrEnum):
    CONTINUE = "continue"
    ATTACK = "attack"
    DEFEND = "defend"
    FLEE = "flee"
    RETRY = "retry"
    COMPLETE = "complete"


class BattleAction(StrEnum):
    ATTACK = "attack"
    DEFEND = "defend"
    FLEE = "flee"


class BattleOutcome(StrEnum):
    CRITICAL_HIT = "critical_hit"
    HIT = "hit"
    MISS = "miss"
    BLOCKED = "blocked"
    GUARD_BROKEN = "guard_broken"
    ESCAPED = "escaped"
    FAILED_TO_ESCAPE = "failed_to_escape"
    INVALID_ACTION = "invalid_action"


@dataclass(frozen=True)
class BattleResult:
    action: str
    dice: int
    outcome: BattleOutcome
    damage: int


def resolve_battle_result(
    *,
    action: str,
    dice: int,
    damage: int,
) -> BattleResult:
    """Resolve a battle action into its deterministic domain outcome."""
    if action == BattleAction.ATTACK:
        outcome = (
            BattleOutcome.CRITICAL_HIT
            if dice >= 18
            else BattleOutcome.HIT
            if dice >= 8
            else BattleOutcome.MISS
        )
        resolved_damage = (
            damage if outcome in {BattleOutcome.HIT, BattleOutcome.CRITICAL_HIT} else 0
        )
    elif action == BattleAction.DEFEND:
        outcome = BattleOutcome.BLOCKED if dice >= 7 else BattleOutcome.GUARD_BROKEN
        resolved_damage = 0 if outcome == BattleOutcome.BLOCKED else damage
    elif action == BattleAction.FLEE:
        outcome = BattleOutcome.ESCAPED if dice >= 10 else BattleOutcome.FAILED_TO_ESCAPE
        resolved_damage = 0 if outcome == BattleOutcome.ESCAPED else damage
    else:
        outcome = BattleOutcome.INVALID_ACTION
        resolved_damage = 0

    return BattleResult(
        action=action,
        dice=dice,
        outcome=outcome,
        damage=resolved_damage,
    )
