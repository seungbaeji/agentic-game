from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from langgraph.graph import StateGraph


@dataclass(frozen=True)
class ScenarioGraphNodes:
    decision: Callable[..., Any]
    flow: Callable[..., Any]
    hitl: Callable[..., Any]
    execute: Callable[..., Any]
    response: Callable[..., Any]
    ask_user: Callable[..., Any]


@dataclass(frozen=True)
class ScenarioAdapter:
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


def build_scenario_adapter_subgraph(adapter: ScenarioAdapter):
    """Build a scenario subgraph from a scenario adapter."""
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
