from __future__ import annotations

from agentic_game.agent.graph.scenario import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.exploration import (
    exploration_ask_user_node,
    exploration_decision_node,
    exploration_decision_route,
    exploration_execute_node,
    exploration_flow_node,
    exploration_hitl_node,
    exploration_response_node,
    exploration_route,
)
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
        route=exploration_route,
        decision_route=exploration_decision_route,
    )
