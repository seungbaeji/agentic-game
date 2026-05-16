from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.graph.scenario import (
    ScenarioAdapter,
    ScenarioGraphNodes,
    build_scenario_adapter_subgraph,
)
from agentic_game.agent.nodes.trade import (
    trade_ask_user_node,
    trade_decision_node,
    trade_decision_route,
    trade_execute_node,
    trade_flow_node,
    trade_hitl_node,
    trade_response_node,
    trade_route,
)
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.state import TradeState

TRADE_DECISION_EDGES = {
    ScenarioNode.FLOW: ScenarioNode.FLOW,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

TRADE_FLOW_EDGES = {
    ScenarioNode.HITL: ScenarioNode.HITL,
    ScenarioNode.EXECUTE: ScenarioNode.EXECUTE,
    ScenarioNode.RESPONSE: ScenarioNode.RESPONSE,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

TRADE_HITL_EDGES = {
    ScenarioNode.DECISION: ScenarioNode.DECISION,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

TRADE_DIRECT_EDGES = [
    (ScenarioNode.EXECUTE, ScenarioNode.RESPONSE),
    (ScenarioNode.RESPONSE, END),
    (ScenarioNode.ASK_USER, END),
]


def make_trade_adapter() -> ScenarioAdapter:
    """Create the graph adapter for the trade scenario."""
    return ScenarioAdapter(
        state_schema=TradeState,
        node_names=ScenarioNode,
        graph_nodes=ScenarioGraphNodes(
            decision=trade_decision_node,
            flow=trade_flow_node,
            hitl=trade_hitl_node,
            execute=trade_execute_node,
            response=trade_response_node,
            ask_user=trade_ask_user_node,
        ),
        route=trade_route,
        flow_edges=TRADE_FLOW_EDGES,
        hitl_edges=TRADE_HITL_EDGES,
        direct_edges=TRADE_DIRECT_EDGES,
        decision_route=trade_decision_route,
        decision_edges=TRADE_DECISION_EDGES,
    )


def build_trade_subgraph():
    """Build the LangGraph subgraph that runs the trade workflow."""
    return build_scenario_adapter_subgraph(make_trade_adapter())
