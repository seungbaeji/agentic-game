from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.graph.scenario import (
    ScenarioAdapter,
    ScenarioGraphNodes,
    build_scenario_adapter_subgraph,
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
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.state import DialogueState

DIALOGUE_DECISION_EDGES = {
    ScenarioNode.FLOW: ScenarioNode.FLOW,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

DIALOGUE_FLOW_EDGES = {
    ScenarioNode.HITL: ScenarioNode.HITL,
    ScenarioNode.EXECUTE: ScenarioNode.EXECUTE,
    ScenarioNode.RESPONSE: ScenarioNode.RESPONSE,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

DIALOGUE_HITL_EDGES = {
    ScenarioNode.DECISION: ScenarioNode.DECISION,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

DIALOGUE_DIRECT_EDGES = [
    (ScenarioNode.EXECUTE, ScenarioNode.RESPONSE),
    (ScenarioNode.RESPONSE, END),
    (ScenarioNode.ASK_USER, END),
]


def make_dialogue_adapter() -> ScenarioAdapter:
    """Create the graph adapter for the dialogue scenario."""
    return ScenarioAdapter(
        state_schema=DialogueState,
        node_names=ScenarioNode,
        graph_nodes=ScenarioGraphNodes(
            decision=dialogue_decision_node,
            flow=dialogue_flow_node,
            hitl=dialogue_hitl_node,
            execute=dialogue_execute_node,
            response=dialogue_response_node,
            ask_user=dialogue_ask_user_node,
        ),
        route=dialogue_route,
        flow_edges=DIALOGUE_FLOW_EDGES,
        hitl_edges=DIALOGUE_HITL_EDGES,
        direct_edges=DIALOGUE_DIRECT_EDGES,
        decision_route=dialogue_decision_route,
        decision_edges=DIALOGUE_DECISION_EDGES,
    )


def build_dialogue_subgraph():
    """Build the LangGraph subgraph that runs the dialogue workflow."""
    return build_scenario_adapter_subgraph(make_dialogue_adapter())
