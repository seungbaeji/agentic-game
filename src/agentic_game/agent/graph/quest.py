from __future__ import annotations

from agentic_game.agent.graph.scenario import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.quest import (
    quest_ask_user_node,
    quest_decision_node,
    quest_execute_node,
    quest_flow_node,
    quest_hitl_node,
    quest_response_node,
)
from agentic_game.agent.nodes.scenario import scenario_decision_route, scenario_route
from agentic_game.agent.state import QuestState


def build_quest_subgraph():
    """Build the LangGraph subgraph that runs the quest workflow."""
    return build_simple_scenario_subgraph(
        state_schema=QuestState,
        graph_nodes=ScenarioGraphNodes(
            decision=quest_decision_node,
            flow=quest_flow_node,
            hitl=quest_hitl_node,
            execute=quest_execute_node,
            response=quest_response_node,
            ask_user=quest_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
