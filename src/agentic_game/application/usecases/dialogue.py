from __future__ import annotations

from dataclasses import dataclass

from agentic_game.application.game_state import GameStateRepository
from agentic_game.domain.dialogue import DialogueEvent
from agentic_game.domain.game_state import NpcMemory

DEFAULT_NPC_ID = "village_elder"


@dataclass(frozen=True, slots=True)
class DialogueMemoryResult:
    npc_id: str
    npc_memory: NpcMemory


def remember_dialogue_event(
    *,
    event: DialogueEvent | None,
    game_state: GameStateRepository,
    npc_id: str = DEFAULT_NPC_ID,
) -> DialogueMemoryResult:
    """Persist deterministic NPC memory for a dialogue event."""
    if event == DialogueEvent.ASK_RUMOR:
        npc_memory = game_state.update_npc(
            npc_id=npc_id,
            memory="old_ruins_rumor",
        )
    elif event == DialogueEvent.ASK_TRADE:
        npc_memory = game_state.update_npc(
            npc_id=npc_id,
            memory="merchant_intro",
        )
    elif event == DialogueEvent.THANK:
        npc_memory = game_state.update_npc(
            npc_id=npc_id,
            relation_delta=1,
            memory="received_thanks",
        )
    else:
        npc_memory = game_state.update_npc(npc_id=npc_id)

    return DialogueMemoryResult(npc_id=npc_id, npc_memory=npc_memory)
