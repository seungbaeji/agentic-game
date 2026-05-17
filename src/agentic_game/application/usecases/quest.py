from __future__ import annotations

from dataclasses import dataclass

from agentic_game.application.game_state import GameStateRepository
from agentic_game.domain.game_state import PlayerState, QuestLog

DEFAULT_QUEST_ID = "old_ruins"
QUEST_REWARD_EXP = 25
QUEST_REWARD_GOLD = 20


@dataclass(frozen=True, slots=True)
class QuestUpdateResult:
    quest_id: str
    quest_log: QuestLog
    player: PlayerState | None = None


def mark_quest_progress(
    *,
    game_state: GameStateRepository,
    quest_id: str = DEFAULT_QUEST_ID,
) -> QuestUpdateResult:
    """Persist quest progress after the objective is reached."""
    quest_log = game_state.update_quest(
        quest_id=quest_id,
        status="ready_to_turn_in",
        progress=100,
    )
    return QuestUpdateResult(quest_id=quest_id, quest_log=quest_log)


def complete_quest(
    *,
    game_state: GameStateRepository,
    quest_id: str = DEFAULT_QUEST_ID,
) -> QuestUpdateResult:
    """Persist quest completion and reward the player."""
    quest_log = game_state.update_quest(
        quest_id=quest_id,
        status="complete",
        progress=100,
    )
    player = game_state.apply_player_delta(
        exp_gain=QUEST_REWARD_EXP,
        gold_change=QUEST_REWARD_GOLD,
    )
    return QuestUpdateResult(
        quest_id=quest_id,
        quest_log=quest_log,
        player=player,
    )
