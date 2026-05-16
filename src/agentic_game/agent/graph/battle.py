from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import StateGraph

from agentic_game.agent.models import BattleNode
from agentic_game.agent.nodes.battle import (
    battle_ask_user_node,
    battle_execute_tool_node,
    battle_flow_node,
    battle_hitl_node,
    battle_route,
    make_battle_decision_node,
    make_battle_response_node,
)
from agentic_game.agent.runtime.tools import ToolInvoker
from agentic_game.agent.state import BattleState
from agentic_game.agent.transitions import (
    BATTLE_DIRECT_EDGES,
    BATTLE_FLOW_EDGES,
    BATTLE_HITL_EDGES,
)
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.battle import BattleResult


def build_battle_subgraph(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleResult],
    random: RandomPort,
):
    """Build the LangGraph subgraph that runs the battle workflow."""
    builder = StateGraph(BattleState)

    builder.add_node(BattleNode.DECISION, make_battle_decision_node(llm))
    builder.add_node(BattleNode.FLOW, battle_flow_node)
    builder.add_node(BattleNode.HITL, battle_hitl_node)

    def execute_with_store(state: BattleState) -> BattleState:
        """Execute the battle tool with dependencies closed over from bootstrap."""
        return battle_execute_tool_node(
            state,
            store=store,
            resolve_battle_tool=resolve_battle_tool,
            resolve_battle_action=resolve_battle_action,
            random=random,
        )

    builder.add_node(BattleNode.EXECUTE, execute_with_store)
    builder.add_node(BattleNode.RESPONSE, make_battle_response_node(llm))
    builder.add_node(BattleNode.ASK_USER, battle_ask_user_node)

    builder.set_entry_point(BattleNode.DECISION)

    builder.add_conditional_edges(
        BattleNode.FLOW,
        battle_route,
        BATTLE_FLOW_EDGES,
    )

    builder.add_conditional_edges(
        BattleNode.HITL,
        battle_route,
        BATTLE_HITL_EDGES,
    )

    for source, target in BATTLE_DIRECT_EDGES:
        builder.add_edge(source, target)

    return builder.compile()
