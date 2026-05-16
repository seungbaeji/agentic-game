from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.decisions import CraftDecision
from agentic_game.agent.models import CraftNode
from agentic_game.agent.prompts import (
    build_craft_decision_prompt,
    build_craft_response_prompt,
)
from agentic_game.agent.routing import craft_node_after_phase
from agentic_game.agent.runtime.tools import ToolInvoker, execute_craft_tool
from agentic_game.agent.state import CraftState
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.craft import CraftEvent, CraftPhase, CraftResult
from agentic_game.flow.craft import (
    resolve_craft_transition,
    serialize_craft_actions,
)
from agentic_game.flow.intent import infer_craft_event


def make_craft_decision_node(llm: LLMPort):
    """Create a LangGraph node that decides the next craft event."""

    def craft_decision_node(state: CraftState) -> CraftState:
        """Decide the craft event from deterministic intent or LLM output."""
        phase = state.get("phase", CraftPhase.SELECT_RECIPE)
        available_actions = serialize_craft_actions(phase)
        user_text = state.get("human_input") or state.get("user_input", "")
        inferred_event = infer_craft_event(phase, user_text)

        if inferred_event is not None:
            return {
                "phase": phase,
                "event": inferred_event,
                "available_actions": available_actions,
                "reason": "user_input에서 명시적인 제작 행동을 감지했습니다.",
                "next_node": CraftNode.FLOW,
            }

        if phase == CraftPhase.SELECT_RECIPE:
            return {
                "phase": phase,
                "event": CraftEvent.CONTINUE,
                "available_actions": available_actions,
                "reason": "제작할 아이템 선택이 필요합니다.",
                "next_node": CraftNode.FLOW,
            }

        if phase == CraftPhase.CRAFT:
            return {
                "phase": phase,
                "available_actions": available_actions,
                "reason": "제작할 아이템 선택이 필요합니다.",
                "next_node": CraftNode.ASK_USER,
            }

        decision = llm.structured_output(
            CraftDecision,
            build_craft_decision_prompt(
                phase=phase,
                available_actions=available_actions,
                user_text=user_text,
            ),
        )

        return {
            "phase": phase,
            "event": decision.event,
            "available_actions": available_actions,
            "reason": decision.reason,
            "next_node": CraftNode.FLOW,
        }

    return craft_decision_node


def craft_flow_node(state: CraftState) -> CraftState:
    """Advance craft phase according to the selected event."""
    phase = state["phase"]
    event = state["event"]
    rule = resolve_craft_transition(phase, event)

    if rule is None:
        return {
            "reason": "현재 제작 phase에서 허용되지 않은 event입니다.",
            "next_node": CraftNode.ASK_USER,
        }

    next_phase = rule.to_phase

    return {
        "phase": next_phase,
        "available_actions": serialize_craft_actions(next_phase),
        "next_node": craft_node_after_phase(next_phase),
    }


def craft_hitl_node(state: CraftState) -> CraftState:
    """Ask for a craft recipe when the user has not provided one."""
    human_input = state.get("human_input", "")
    if not infer_craft_event(CraftPhase.CRAFT, human_input):
        return {
            "response": ("HITL 필요: 제작할 아이템을 선택하세요. 가능한 선택: potion / sword"),
            "next_node": CraftNode.ASK_USER,
        }

    return {
        "next_node": CraftNode.DECISION,
    }


def craft_execute_tool_node(
    state: CraftState,
    *,
    store: StorePort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftResult],
    random: RandomPort,
) -> CraftState:
    """Invoke the craft tool and persist its raw, LLM, and UI payloads."""
    return execute_craft_tool(
        state=state,
        store=store,
        craft_item_tool=craft_item_tool,
        craft_item=craft_item,
        random=random,
    )


def make_craft_response_node(llm: LLMPort):
    """Create a LangGraph node that turns craft state into a response."""

    def craft_response_node(state: CraftState) -> CraftState:
        """Return an existing concrete response or ask the LLM to summarize."""
        existing_response = state.get("response")
        if existing_response:
            return {
                "response": existing_response,
            }

        response = llm.respond(build_craft_response_prompt(state))

        return {
            "response": response,
        }

    return craft_response_node


def craft_ask_user_node(state: CraftState) -> CraftState:
    """Return a user-facing prompt for a craft recipe."""
    return {
        "response": "제작할 아이템을 선택해 주세요. 가능한 선택: 포션 / 검",
    }


def craft_route(state: CraftState) -> str:
    """Read the next craft node selected by the previous node."""
    return state["next_node"]


def craft_decision_route(state: CraftState) -> str:
    """Route after craft decision, defaulting to the flow node."""
    return state.get("next_node", CraftNode.FLOW)
