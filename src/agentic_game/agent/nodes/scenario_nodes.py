from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from agentic_game.flow.transitions import resolve_transition, serialize_actions
from agentic_game.scenarios.spec import ScenarioNode, ScenarioSpec

type ScenarioState = dict[str, Any]


def make_decision_node[PhaseT, EventT](
    *,
    default_phase: PhaseT,
    serialize_actions: Callable[[PhaseT], Any],
    detect_event: Callable[[PhaseT, str], EventT | None],
    detected_reason: str,
    fallback_reason: str,
    default_events: Mapping[PhaseT, tuple[EventT, str]] | None = None,
) -> Callable[[ScenarioState], ScenarioState]:
    """Create a deterministic decision node for simple scenarios."""

    def decision_node(state: ScenarioState) -> ScenarioState:
        phase = state.get("phase", default_phase)
        available_actions = serialize_actions(phase)
        user_text = state.get("human_input") or state.get("user_input", "")
        detected_event = detect_event(phase, user_text)

        if detected_event is not None:
            return {
                "phase": phase,
                "event": detected_event,
                "available_actions": available_actions,
                "reason": detected_reason,
                "next_node": ScenarioNode.FLOW,
            }

        if default_events is not None and phase in default_events:
            event, reason = default_events[phase]
            return {
                "phase": phase,
                "event": event,
                "available_actions": available_actions,
                "reason": reason,
                "next_node": ScenarioNode.FLOW,
            }

        return {
            "phase": phase,
            "available_actions": available_actions,
            "reason": fallback_reason,
            "next_node": ScenarioNode.ASK_USER,
        }

    return decision_node


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


def make_hitl_node[PhaseT, EventT](
    *,
    default_phase: PhaseT,
    detect_event: Callable[[PhaseT, str], EventT | None],
    prompt: str,
) -> Callable[[ScenarioState], ScenarioState]:
    """Create a HITL node that asks for input until an event can be detected."""

    def hitl_node(state: ScenarioState) -> ScenarioState:
        phase = state.get("phase", default_phase)
        human_input = state.get("human_input", "")

        if detect_event(phase, human_input) is None:
            return {
                "response": prompt,
                "next_node": ScenarioNode.ASK_USER,
            }

        return {
            "next_node": ScenarioNode.DECISION,
        }

    return hitl_node


def make_ask_user_node(prompt: str) -> Callable[[ScenarioState], ScenarioState]:
    """Create an ask-user node that returns a static scenario prompt."""

    def ask_user_node(state: ScenarioState) -> ScenarioState:
        return {
            "response": prompt,
        }

    return ask_user_node


def scenario_route(state: ScenarioState) -> str:
    """Read the next scenario node selected by the previous node."""
    return state["next_node"]


def scenario_decision_route(state: ScenarioState) -> str:
    """Route after a scenario decision, defaulting to the flow node."""
    return state.get("next_node", ScenarioNode.FLOW)
