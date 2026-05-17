from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.craft import (
    craft_ask_user_node,
    craft_execute_tool_node,
    craft_flow_node,
    craft_hitl_node,
    make_craft_decision_node,
    make_craft_response_node,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.state import CraftState
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.application.usecases.craft import CraftItemResult
from agentic_game.engine.tool_runner import ToolInvoker


def build_craft_subgraph(
    store: StorePort,
    llm: LLMPort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftItemResult],
    random: RandomPort,
):
    """Build the LangGraph subgraph that runs the craft workflow."""
    def execute_with_store(state: CraftState) -> CraftState:
        """Execute the craft tool with dependencies closed over from bootstrap."""
        return craft_execute_tool_node(
            state,
            store=store,
            llm=llm,
            craft_item_tool=craft_item_tool,
            craft_item=craft_item,
            random=random,
        )

    return build_simple_scenario_subgraph(
        state_schema=CraftState,
        graph_nodes=ScenarioGraphNodes(
            decision=make_craft_decision_node(llm),
            flow=craft_flow_node,
            hitl=craft_hitl_node,
            execute=execute_with_store,
            response=make_craft_response_node(llm),
            ask_user=craft_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
