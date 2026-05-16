from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.graph.scenario import (
    ScenarioAdapter,
    ScenarioGraphNodes,
    build_scenario_adapter_subgraph,
)
from agentic_game.agent.nodes.skill_training import (
    skill_training_ask_user_node,
    skill_training_decision_node,
    skill_training_decision_route,
    skill_training_execute_node,
    skill_training_flow_node,
    skill_training_hitl_node,
    skill_training_response_node,
    skill_training_route,
)
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.state import SkillTrainingState

SKILL_TRAINING_DECISION_EDGES = {
    ScenarioNode.FLOW: ScenarioNode.FLOW,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

SKILL_TRAINING_FLOW_EDGES = {
    ScenarioNode.HITL: ScenarioNode.HITL,
    ScenarioNode.EXECUTE: ScenarioNode.EXECUTE,
    ScenarioNode.RESPONSE: ScenarioNode.RESPONSE,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

SKILL_TRAINING_HITL_EDGES = {
    ScenarioNode.DECISION: ScenarioNode.DECISION,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

SKILL_TRAINING_DIRECT_EDGES = [
    (ScenarioNode.EXECUTE, ScenarioNode.RESPONSE),
    (ScenarioNode.RESPONSE, END),
    (ScenarioNode.ASK_USER, END),
]


def make_skill_training_adapter() -> ScenarioAdapter:
    """Create the graph adapter for the skill training scenario."""
    return ScenarioAdapter(
        state_schema=SkillTrainingState,
        node_names=ScenarioNode,
        graph_nodes=ScenarioGraphNodes(
            decision=skill_training_decision_node,
            flow=skill_training_flow_node,
            hitl=skill_training_hitl_node,
            execute=skill_training_execute_node,
            response=skill_training_response_node,
            ask_user=skill_training_ask_user_node,
        ),
        route=skill_training_route,
        flow_edges=SKILL_TRAINING_FLOW_EDGES,
        hitl_edges=SKILL_TRAINING_HITL_EDGES,
        direct_edges=SKILL_TRAINING_DIRECT_EDGES,
        decision_route=skill_training_decision_route,
        decision_edges=SKILL_TRAINING_DECISION_EDGES,
    )


def build_skill_training_subgraph():
    """Build the LangGraph subgraph that runs the skill training workflow."""
    return build_scenario_adapter_subgraph(make_skill_training_adapter())
