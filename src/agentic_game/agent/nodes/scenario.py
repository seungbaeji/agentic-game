from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agentic_game.agent.scenario import ScenarioNode, ScenarioSpec
from agentic_game.flow.transitions import resolve_transition, serialize_actions

type ScenarioState = dict[str, Any]


def make_flow_node[PhaseT, EventT, NodeT](
    *,
    spec: ScenarioSpec[PhaseT, EventT],
    node_for: Callable[[ScenarioNode], NodeT],
    invalid_event_message: str,
) -> Callable[[ScenarioState], ScenarioState]:
    """Create a flow node that advances phase from scenario transition data."""

    def flow_node(state: ScenarioState) -> ScenarioState:
        phase = state["phase"]
        event = state["event"]
        rule = resolve_transition(spec.transitions, phase, event)

        if rule is None:
            return {
                "reason": invalid_event_message,
                "next_node": node_for(ScenarioNode.ASK_USER),
            }

        next_phase = rule.to_phase
        next_scenario_node = spec.phase_to_node.get(next_phase, ScenarioNode.RESPONSE)

        return {
            "phase": next_phase,
            "available_actions": serialize_actions(spec.transitions, next_phase),
            "next_node": node_for(next_scenario_node),
        }

    return flow_node


def scenario_route(state: ScenarioState) -> str:
    """Read the next scenario node selected by the previous node."""
    return state["next_node"]


def scenario_decision_route(state: ScenarioState) -> str:
    """Route after a scenario decision, defaulting to the flow node."""
    return state.get("next_node", ScenarioNode.FLOW)
