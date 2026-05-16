from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.graph.scenario import (
    ScenarioAdapter,
    ScenarioGraphNodes,
    build_scenario_adapter_subgraph,
)
from agentic_game.agent.nodes.quest import (
    quest_ask_user_node,
    quest_decision_node,
    quest_decision_route,
    quest_execute_node,
    quest_flow_node,
    quest_hitl_node,
    quest_response_node,
    quest_route,
)
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.state import QuestState

QUEST_DECISION_EDGES = {
    ScenarioNode.FLOW: ScenarioNode.FLOW,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

QUEST_FLOW_EDGES = {
    ScenarioNode.HITL: ScenarioNode.HITL,
    ScenarioNode.EXECUTE: ScenarioNode.EXECUTE,
    ScenarioNode.RESPONSE: ScenarioNode.RESPONSE,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

QUEST_HITL_EDGES = {
    ScenarioNode.DECISION: ScenarioNode.DECISION,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

QUEST_DIRECT_EDGES = [
    (ScenarioNode.EXECUTE, ScenarioNode.RESPONSE),
    (ScenarioNode.RESPONSE, END),
    (ScenarioNode.ASK_USER, END),
]


def make_quest_adapter() -> ScenarioAdapter:
    """Create the graph adapter for the quest scenario."""
    return ScenarioAdapter(
        state_schema=QuestState,
        node_names=ScenarioNode,
        graph_nodes=ScenarioGraphNodes(
            decision=quest_decision_node,
            flow=quest_flow_node,
            hitl=quest_hitl_node,
            execute=quest_execute_node,
            response=quest_response_node,
            ask_user=quest_ask_user_node,
        ),
        route=quest_route,
        flow_edges=QUEST_FLOW_EDGES,
        hitl_edges=QUEST_HITL_EDGES,
        direct_edges=QUEST_DIRECT_EDGES,
        decision_route=quest_decision_route,
        decision_edges=QUEST_DECISION_EDGES,
    )


def build_quest_subgraph():
    """Build the LangGraph subgraph that runs the quest workflow."""
    return build_scenario_adapter_subgraph(make_quest_adapter())
