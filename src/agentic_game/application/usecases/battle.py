from __future__ import annotations

from dataclasses import dataclass

from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.ports import RandomPort
from agentic_game.domain.battle import (
    BattleAction,
    BattleOutcome,
    BattleResult,
    resolve_battle_result,
)
from agentic_game.domain.game_state import PlayerState


@dataclass(frozen=True, slots=True)
class PlayerDelta:
    hp_change: int = 0
    exp_gain: int = 0


@dataclass(frozen=True, slots=True)
class BattleActionResult:
    battle: BattleResult
    player_delta: PlayerDelta | None = None
    player: PlayerState | None = None

    @property
    def action(self) -> str:
        return self.battle.action

    @property
    def dice(self) -> int:
        return self.battle.dice

    @property
    def outcome(self) -> BattleOutcome:
        return self.battle.outcome

    @property
    def damage(self) -> int:
        return self.battle.damage


def resolve_battle_action(
    action: str,
    *,
    random: RandomPort,
) -> BattleActionResult:
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
    result = resolve_battle_result(action=action, dice=dice, damage=damage)
    return BattleActionResult(battle=result)


def resolve_battle_action_and_store_player(
    action: str,
    *,
    random: RandomPort,
    game_state: GameStateRepository,
) -> BattleActionResult:
    """Resolve a battle action and persist player HP/EXP changes."""
    result = resolve_battle_action(action, random=random).battle
    delta = player_delta_for_battle(result)
    player = game_state.apply_player_delta(
        hp_change=delta.hp_change,
        exp_gain=delta.exp_gain,
    )
    return BattleActionResult(
        battle=result,
        player_delta=delta,
        player=player,
    )


def player_delta_for_battle(result: BattleResult) -> PlayerDelta:
    """Calculate player HP/EXP changes from a battle result."""
    if result.outcome == BattleOutcome.CRITICAL_HIT:
        return PlayerDelta(exp_gain=20)
    if result.outcome == BattleOutcome.HIT:
        return PlayerDelta(exp_gain=10)
    if result.outcome in {
        BattleOutcome.GUARD_BROKEN,
        BattleOutcome.FAILED_TO_ESCAPE,
    }:
        return PlayerDelta(hp_change=-result.damage)
    return PlayerDelta()
