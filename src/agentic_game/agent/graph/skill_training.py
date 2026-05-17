from __future__ import annotations

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.nodes.skill_training import (
    make_skill_training_execute_node,
    make_skill_training_response_node,
    skill_training_ask_user_node,
    skill_training_decision_node,
    skill_training_flow_node,
    skill_training_hitl_node,
)
from agentic_game.agent.state import SkillTrainingState
from agentic_game.application.ports import StorePort


def build_skill_training_subgraph(store: StorePort):
    """Build the LangGraph subgraph that runs the skill training workflow."""
    return build_simple_scenario_subgraph(
        state_schema=SkillTrainingState,
        graph_nodes=ScenarioGraphNodes(
            decision=skill_training_decision_node,
            flow=skill_training_flow_node,
            hitl=skill_training_hitl_node,
            execute=make_skill_training_execute_node(store),
            response=make_skill_training_response_node(store),
            ask_user=skill_training_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
