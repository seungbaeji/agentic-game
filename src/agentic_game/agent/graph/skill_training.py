from __future__ import annotations

from agentic_game.agent.graph.scenario import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
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
from agentic_game.agent.state import SkillTrainingState


def build_skill_training_subgraph():
    """Build the LangGraph subgraph that runs the skill training workflow."""
    return build_simple_scenario_subgraph(
        state_schema=SkillTrainingState,
        graph_nodes=ScenarioGraphNodes(
            decision=skill_training_decision_node,
            flow=skill_training_flow_node,
            hitl=skill_training_hitl_node,
            execute=skill_training_execute_node,
            response=skill_training_response_node,
            ask_user=skill_training_ask_user_node,
        ),
        route=skill_training_route,
        decision_route=skill_training_decision_route,
    )
