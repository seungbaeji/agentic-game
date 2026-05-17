from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from agentic_game.agent.state import BattleState, CraftState
from agentic_game.agent.types import PhasePayloadRefs, RuntimeState, ToolInput
from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.ports import RandomPort, StorePort
from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.scenarios.spec import ScenarioNode
from agentic_game.tools.types import ToolResult


class ToolInvoker(Protocol):
    def invoke(self, input: ToolInput) -> ToolResult:
        """Invoke a hydrated LangChain tool and return its internal result."""
        ...


_BATTLE_ACTION_BY_EVENT = {
    BattleEvent.ATTACK: "attack",
    BattleEvent.DEFEND: "defend",
    BattleEvent.FLEE: "flee",
}

_CRAFT_RECIPE_BY_EVENT = {
    CraftEvent.CRAFT_POTION: "potion",
    CraftEvent.CRAFT_SWORD: "sword",
}


def persist_tool_result(
    *,
    store: StorePort,
    state: RuntimeState,
    subgraph: str,
    phase: str,
    tool_result: ToolResult,
) -> PhasePayloadRefs:
    """Persist raw, LLM, and UI tool payloads and return updated refs."""
    raw_update = store.persist_phase_payload(
        state=state,
        subgraph=subgraph,
        phase=phase,
        payload_name="raw",
        value=tool_result.raw,
    )
    llm_update = store.persist_phase_payload(
        state={**state, **raw_update},
        subgraph=subgraph,
        phase=phase,
        payload_name="llm",
        value=tool_result.llm,
    )
    return store.persist_phase_payload(
        state={**state, **llm_update},
        subgraph=subgraph,
        phase=phase,
        payload_name="ui",
        value=tool_result.ui,
    )


def execute_battle_tool(
    *,
    state: BattleState,
    store: StorePort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., object],
    random: RandomPort,
) -> BattleState:
    """Invoke the battle tool and return the battle graph state update."""
    event = state["event"]
    action = _BATTLE_ACTION_BY_EVENT.get(event)
    if action is None:
        return {
            "reason": f"tool로 실행할 수 없는 battle event입니다: {event}",
            "next_node": ScenarioNode.ASK_USER,
        }

    tool_result = resolve_battle_tool.invoke({
        "action": action,
        "resolve_battle_action": resolve_battle_action,
        "random": random,
        "game_state": GameStateRepository(store),
    })
    ref_update = persist_tool_result(
        store=store,
        state=state,
        subgraph="battle",
        phase=BattlePhase.RESOLVE.value,
        tool_result=tool_result,
    )

    return {
        "latest_refs": ref_update["latest_refs"],
        "history_refs": ref_update["history_refs"],
        "response": tool_result.llm["summary"],
        "next_node": ScenarioNode.RESPONSE,
    }


def execute_craft_tool(
    *,
    state: CraftState,
    store: StorePort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., object],
    random: RandomPort,
) -> CraftState:
    """Invoke the craft tool and return the craft graph state update."""
    event = state["event"]
    recipe = _CRAFT_RECIPE_BY_EVENT.get(event)
    if recipe is None:
        return {
            "reason": f"tool로 실행할 수 없는 craft event입니다: {event}",
            "next_node": ScenarioNode.ASK_USER,
        }

    tool_result = craft_item_tool.invoke({
        "recipe": recipe,
        "craft_item": craft_item,
        "random": random,
        "game_state": GameStateRepository(store),
    })
    ref_update = persist_tool_result(
        store=store,
        state=state,
        subgraph="craft",
        phase=CraftPhase.RESULT.value,
        tool_result=tool_result,
    )

    return {
        "latest_refs": ref_update["latest_refs"],
        "history_refs": ref_update["history_refs"],
        "response": tool_result.llm["summary"],
        "next_node": ScenarioNode.RESPONSE,
    }
