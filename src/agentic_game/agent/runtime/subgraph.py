from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.graph.battle import build_battle_subgraph
from agentic_game.agent.graph.craft import build_craft_subgraph
from agentic_game.agent.models import ParentNode, SubgraphName
from agentic_game.agent.runtime.tools import ToolInvoker
from agentic_game.agent.state import BattleState, CraftState, ParentState
from agentic_game.agent.types import RuntimePayload
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.battle import BattlePhase, BattleResult
from agentic_game.domain.craft import CraftPhase, CraftResult
from agentic_game.flow.craft import answer_craft_result_question


def remove_runtime_routing(state: BattleState | CraftState) -> RuntimePayload:
    """Remove routing-only keys before persisting graph state."""
    persisted_state = dict(state)
    persisted_state.pop("next_node", None)
    return persisted_state


def load_latest_craft_result(
    store: StorePort,
    saved_state: CraftState,
) -> RuntimePayload | None:
    """Load the latest persisted craft UI result when one is referenced."""
    latest_refs = saved_state.get("latest_refs", {})
    if "result.ui" not in latest_refs:
        return None

    try:
        latest_result = store.get(
            namespace=("craft", "result", "ui"),
            key="latest",
        )
    except KeyError:
        return None

    return latest_result


def make_battle_wrapper(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleResult],
    random: RandomPort,
):
    """Create the parent node that invokes and persists the battle subgraph."""
    battle_graph = build_battle_subgraph(
        store,
        llm,
        resolve_battle_tool,
        resolve_battle_action,
        random,
    )

    def battle_subgraph_node(state: ParentState) -> ParentState:
        """Load battle state, run the battle subgraph, and persist the result."""
        refs = dict(state.get("store_refs", {}))
        state_ref = refs.get("battle_state")

        if state_ref:
            saved_state = store.get(namespace=("battle", "state"), key="latest")
        else:
            saved_state = {
                "phase": BattlePhase.PREPARE,
                "latest_refs": {},
                "history_refs": {},
            }

        battle_state: BattleState = {
            **saved_state,
            "user_input": state.get("user_input", ""),
            "human_input": state.get("user_input", ""),
        }

        result: BattleState = battle_graph.invoke(battle_state)

        refs["battle_state"] = store.put(
            namespace=("battle", "state"),
            key="latest",
            value=remove_runtime_routing(result),
        )

        return {
            "current_subgraph": SubgraphName.BATTLE,
            "store_refs": refs,
            "response": result.get("response", ""),
            "next_node": ParentNode.RESPONSE,
        }

    return battle_subgraph_node


def make_craft_wrapper(
    store: StorePort,
    llm: LLMPort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftResult],
    random: RandomPort,
):
    """Create the parent node that invokes and persists the craft subgraph."""
    craft_graph = build_craft_subgraph(
        store,
        llm,
        craft_item_tool,
        craft_item,
        random,
    )

    def craft_subgraph_node(state: ParentState) -> ParentState:
        """Load craft state, answer follow-ups, run craft graph, and persist."""
        refs = dict(state.get("store_refs", {}))
        state_ref = refs.get("craft_state")

        if state_ref:
            saved_state = store.get(namespace=("craft", "state"), key="latest")
        else:
            saved_state = {
                "phase": CraftPhase.SELECT_RECIPE,
                "latest_refs": {},
                "history_refs": {},
            }

        followup_response = answer_craft_result_question(
            phase=saved_state.get("phase", CraftPhase.SELECT_RECIPE),
            latest_result=load_latest_craft_result(store, saved_state),
            user_input=state.get("user_input", ""),
        )
        if followup_response is not None:
            return {
                "current_subgraph": SubgraphName.CRAFT,
                "store_refs": refs,
                "response": followup_response,
                "next_node": ParentNode.RESPONSE,
            }

        craft_state: CraftState = {
            **saved_state,
            "user_input": state.get("user_input", ""),
            "human_input": state.get("user_input", ""),
        }

        result: CraftState = craft_graph.invoke(craft_state)

        refs["craft_state"] = store.put(
            namespace=("craft", "state"),
            key="latest",
            value=remove_runtime_routing(result),
        )

        return {
            "current_subgraph": SubgraphName.CRAFT,
            "store_refs": refs,
            "response": result.get("response", ""),
            "next_node": ParentNode.RESPONSE,
        }

    return craft_subgraph_node
