from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import StateGraph

from agentic_game.agent.models import CraftNode
from agentic_game.agent.nodes.craft import (
    craft_ask_user_node,
    craft_decision_route,
    craft_execute_tool_node,
    craft_flow_node,
    craft_hitl_node,
    craft_route,
    make_craft_decision_node,
    make_craft_response_node,
)
from agentic_game.agent.runtime.tools import ToolInvoker
from agentic_game.agent.state import CraftState
from agentic_game.agent.transitions import (
    CRAFT_DECISION_EDGES,
    CRAFT_DIRECT_EDGES,
    CRAFT_FLOW_EDGES,
    CRAFT_HITL_EDGES,
)
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.craft import CraftResult


def build_craft_subgraph(
    store: StorePort,
    llm: LLMPort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftResult],
    random: RandomPort,
):
    """Build the LangGraph subgraph that runs the craft workflow."""
    builder = StateGraph(CraftState)

    builder.add_node(CraftNode.DECISION, make_craft_decision_node(llm))
    builder.add_node(CraftNode.FLOW, craft_flow_node)
    builder.add_node(CraftNode.HITL, craft_hitl_node)

    def execute_with_store(state: CraftState) -> CraftState:
        """Execute the craft tool with dependencies closed over from bootstrap."""
        return craft_execute_tool_node(
            state,
            store=store,
            craft_item_tool=craft_item_tool,
            craft_item=craft_item,
            random=random,
        )

    builder.add_node(CraftNode.EXECUTE, execute_with_store)
    builder.add_node(CraftNode.RESPONSE, make_craft_response_node(llm))
    builder.add_node(CraftNode.ASK_USER, craft_ask_user_node)

    builder.set_entry_point(CraftNode.DECISION)
    builder.add_conditional_edges(
        CraftNode.DECISION,
        craft_decision_route,
        CRAFT_DECISION_EDGES,
    )

    builder.add_conditional_edges(
        CraftNode.FLOW,
        craft_route,
        CRAFT_FLOW_EDGES,
    )

    builder.add_conditional_edges(
        CraftNode.HITL,
        craft_route,
        CRAFT_HITL_EDGES,
    )

    for source, target in CRAFT_DIRECT_EDGES:
        builder.add_edge(source, target)

    return builder.compile()
