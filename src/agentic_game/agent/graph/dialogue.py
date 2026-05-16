from __future__ import annotations

from agentic_game.agent.graph.scenario import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.dialogue import (
    dialogue_ask_user_node,
    dialogue_decision_node,
    dialogue_decision_route,
    dialogue_execute_node,
    dialogue_flow_node,
    dialogue_hitl_node,
    dialogue_response_node,
    dialogue_route,
)
from agentic_game.agent.state import DialogueState


def build_dialogue_subgraph():
    """Build the LangGraph subgraph that runs the dialogue workflow."""
    return build_simple_scenario_subgraph(
        state_schema=DialogueState,
        graph_nodes=ScenarioGraphNodes(
            decision=dialogue_decision_node,
            flow=dialogue_flow_node,
            hitl=dialogue_hitl_node,
            execute=dialogue_execute_node,
            response=dialogue_response_node,
            ask_user=dialogue_ask_user_node,
        ),
        route=dialogue_route,
        decision_route=dialogue_decision_route,
    )
