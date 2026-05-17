from __future__ import annotations

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.dialogue import (
    dialogue_ask_user_node,
    dialogue_decision_node,
    dialogue_execute_node,
    dialogue_flow_node,
    dialogue_hitl_node,
    make_dialogue_response_node,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.state import DialogueState
from agentic_game.application.ports import StorePort


def build_dialogue_subgraph(store: StorePort):
    """Build the LangGraph subgraph that runs the dialogue workflow."""
    return build_simple_scenario_subgraph(
        state_schema=DialogueState,
        graph_nodes=ScenarioGraphNodes(
            decision=dialogue_decision_node,
            flow=dialogue_flow_node,
            hitl=dialogue_hitl_node,
            execute=dialogue_execute_node,
            response=make_dialogue_response_node(store),
            ask_user=dialogue_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
