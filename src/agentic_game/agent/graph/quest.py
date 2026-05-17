from __future__ import annotations

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.quest import (
    make_quest_execute_node,
    make_quest_response_node,
    quest_ask_user_node,
    quest_decision_node,
    quest_flow_node,
    quest_hitl_node,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.state import QuestState
from agentic_game.application.ports import StorePort


def build_quest_subgraph(store: StorePort):
    """Build the LangGraph subgraph that runs the quest workflow."""
    return build_simple_scenario_subgraph(
        state_schema=QuestState,
        graph_nodes=ScenarioGraphNodes(
            decision=quest_decision_node,
            flow=quest_flow_node,
            hitl=quest_hitl_node,
            execute=make_quest_execute_node(store),
            response=make_quest_response_node(store),
            ask_user=quest_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
