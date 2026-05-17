from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from langgraph.graph import END, StateGraph

from agentic_game.scenarios.spec import ScenarioNode


@dataclass(frozen=True)
class ScenarioGraphNodes:
    decision: Callable[..., Any]
    flow: Callable[..., Any]
    hitl: Callable[..., Any]
    execute: Callable[..., Any]
    response: Callable[..., Any]
    ask_user: Callable[..., Any]


@dataclass(frozen=True)
class ScenarioGraphDefinition:
    state_schema: type[Any]
    node_names: type[Any]
    graph_nodes: ScenarioGraphNodes
    route: Callable[[Any], Any]
    flow_edges: Mapping[Any, Any]
    hitl_edges: Mapping[Any, Any]
    direct_edges: Sequence[tuple[Any, Any]]
    decision_route: Callable[[Any], Any] | None = None
    decision_edges: Mapping[Any, Any] | None = None


def build_scenario_subgraph(
    *,
    state_schema: type[Any],
    node_names: type[Any],
    graph_nodes: ScenarioGraphNodes,
    route: Callable[[Any], Any],
    flow_edges: Mapping[Any, Any],
    hitl_edges: Mapping[Any, Any],
    direct_edges: Sequence[tuple[Any, Any]],
    decision_route: Callable[[Any], Any] | None = None,
    decision_edges: Mapping[Any, Any] | None = None,
):
    """Build a scenario subgraph from shared node roles and edge tables."""
    builder = StateGraph(state_schema)

    builder.add_node(node_names.DECISION, graph_nodes.decision)
    builder.add_node(node_names.FLOW, graph_nodes.flow)
    builder.add_node(node_names.HITL, graph_nodes.hitl)
    builder.add_node(node_names.EXECUTE, graph_nodes.execute)
    builder.add_node(node_names.RESPONSE, graph_nodes.response)
    builder.add_node(node_names.ASK_USER, graph_nodes.ask_user)

    builder.set_entry_point(node_names.DECISION)

    if decision_route is not None and decision_edges is not None:
        builder.add_conditional_edges(
            node_names.DECISION,
            decision_route,
            decision_edges,
        )

    builder.add_conditional_edges(
        node_names.FLOW,
        route,
        flow_edges,
    )

    builder.add_conditional_edges(
        node_names.HITL,
        route,
        hitl_edges,
    )

    for source, target in direct_edges:
        builder.add_edge(source, target)

    return builder.compile()


def build_scenario_definition_subgraph(adapter: ScenarioGraphDefinition):
    """Build a scenario subgraph from a scenario graph definition."""
    return build_scenario_subgraph(
        state_schema=adapter.state_schema,
        node_names=adapter.node_names,
        graph_nodes=adapter.graph_nodes,
        route=adapter.route,
        flow_edges=adapter.flow_edges,
        hitl_edges=adapter.hitl_edges,
        direct_edges=adapter.direct_edges,
        decision_route=adapter.decision_route,
        decision_edges=adapter.decision_edges,
    )


SIMPLE_SCENARIO_DECISION_EDGES = {
    ScenarioNode.FLOW: ScenarioNode.FLOW,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

SIMPLE_SCENARIO_FLOW_EDGES = {
    ScenarioNode.HITL: ScenarioNode.HITL,
    ScenarioNode.EXECUTE: ScenarioNode.EXECUTE,
    ScenarioNode.RESPONSE: ScenarioNode.RESPONSE,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

SIMPLE_SCENARIO_HITL_EDGES = {
    ScenarioNode.DECISION: ScenarioNode.DECISION,
    ScenarioNode.ASK_USER: ScenarioNode.ASK_USER,
}

SIMPLE_SCENARIO_DIRECT_EDGES = [
    (ScenarioNode.EXECUTE, ScenarioNode.RESPONSE),
    (ScenarioNode.RESPONSE, END),
    (ScenarioNode.ASK_USER, END),
]


def build_simple_scenario_subgraph(
    *,
    state_schema: type[Any],
    graph_nodes: ScenarioGraphNodes,
    route: Callable[[Any], Any],
    decision_route: Callable[[Any], Any],
):
    """Build a subgraph for scenarios that use the standard ScenarioNode shape."""
    return build_scenario_definition_subgraph(
        ScenarioGraphDefinition(
            state_schema=state_schema,
            node_names=ScenarioNode,
            graph_nodes=graph_nodes,
            route=route,
            flow_edges=SIMPLE_SCENARIO_FLOW_EDGES,
            hitl_edges=SIMPLE_SCENARIO_HITL_EDGES,
            direct_edges=SIMPLE_SCENARIO_DIRECT_EDGES,
            decision_route=decision_route,
            decision_edges=SIMPLE_SCENARIO_DECISION_EDGES,
        )
    )
