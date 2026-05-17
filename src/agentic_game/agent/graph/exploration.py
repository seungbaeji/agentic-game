from __future__ import annotations

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.exploration import (
    exploration_ask_user_node,
    exploration_decision_node,
    exploration_execute_node,
    exploration_flow_node,
    exploration_hitl_node,
    exploration_response_node,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.state import ExplorationState


def build_exploration_subgraph():
    """Build the LangGraph subgraph that runs the exploration workflow."""
    return build_simple_scenario_subgraph(
        state_schema=ExplorationState,
        graph_nodes=ScenarioGraphNodes(
            decision=exploration_decision_node,
            flow=exploration_flow_node,
            hitl=exploration_hitl_node,
            execute=exploration_execute_node,
            response=exploration_response_node,
            ask_user=exploration_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
