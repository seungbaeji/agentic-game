from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphDefinition,
    ScenarioGraphNodes,
    build_scenario_definition_subgraph,
)
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
from agentic_game.agent.state import CraftState
from agentic_game.agent.transitions import (
    CRAFT_DECISION_EDGES,
    CRAFT_DIRECT_EDGES,
    CRAFT_FLOW_EDGES,
    CRAFT_HITL_EDGES,
)
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.craft import CraftResult
from agentic_game.engine.tool_runner import ToolInvoker


def make_craft_graph_definition(
    *,
    llm: LLMPort,
    execute: Callable[[CraftState], CraftState],
) -> ScenarioGraphDefinition:
    """Create the graph definition for the craft scenario."""
    return ScenarioGraphDefinition(
        state_schema=CraftState,
        node_names=CraftNode,
        graph_nodes=ScenarioGraphNodes(
            decision=make_craft_decision_node(llm),
            flow=craft_flow_node,
            hitl=craft_hitl_node,
            execute=execute,
            response=make_craft_response_node(llm),
            ask_user=craft_ask_user_node,
        ),
        route=craft_route,
        flow_edges=CRAFT_FLOW_EDGES,
        hitl_edges=CRAFT_HITL_EDGES,
        direct_edges=CRAFT_DIRECT_EDGES,
        decision_route=craft_decision_route,
        decision_edges=CRAFT_DECISION_EDGES,
    )


def build_craft_subgraph(
    store: StorePort,
    llm: LLMPort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftResult],
    random: RandomPort,
):
    """Build the LangGraph subgraph that runs the craft workflow."""
    def execute_with_store(state: CraftState) -> CraftState:
        """Execute the craft tool with dependencies closed over from bootstrap."""
        return craft_execute_tool_node(
            state,
            store=store,
            craft_item_tool=craft_item_tool,
            craft_item=craft_item,
            random=random,
        )

    return build_scenario_definition_subgraph(
        make_craft_graph_definition(llm=llm, execute=execute_with_store)
    )
