from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.graph.scenario import (
    ScenarioAdapter,
    ScenarioGraphNodes,
    build_scenario_adapter_subgraph,
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
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.state import ExplorationState

EXPLORATION_DECISION_EDGES = {
    ScenarioNode.FLOW: ScenarioNode.FLOW,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

EXPLORATION_FLOW_EDGES = {
    ScenarioNode.HITL: ScenarioNode.HITL,
    ScenarioNode.EXECUTE: ScenarioNode.EXECUTE,
    ScenarioNode.RESPONSE: ScenarioNode.RESPONSE,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

EXPLORATION_HITL_EDGES = {
    ScenarioNode.DECISION: ScenarioNode.DECISION,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

EXPLORATION_DIRECT_EDGES = [
    (ScenarioNode.EXECUTE, ScenarioNode.RESPONSE),
    (ScenarioNode.RESPONSE, END),
    (ScenarioNode.ASK_USER, END),
]


def make_exploration_adapter() -> ScenarioAdapter:
    """Create the graph adapter for the exploration scenario."""
    return ScenarioAdapter(
        state_schema=ExplorationState,
        node_names=ScenarioNode,
        graph_nodes=ScenarioGraphNodes(
            decision=exploration_decision_node,
            flow=exploration_flow_node,
            hitl=exploration_hitl_node,
            execute=exploration_execute_node,
            response=exploration_response_node,
            ask_user=exploration_ask_user_node,
        ),
        route=exploration_route,
        flow_edges=EXPLORATION_FLOW_EDGES,
        hitl_edges=EXPLORATION_HITL_EDGES,
        direct_edges=EXPLORATION_DIRECT_EDGES,
        decision_route=exploration_decision_route,
        decision_edges=EXPLORATION_DECISION_EDGES,
    )


def build_exploration_subgraph():
    """Build the LangGraph subgraph that runs the exploration workflow."""
    return build_scenario_adapter_subgraph(make_exploration_adapter())
