from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.decisions import CraftDecision
from agentic_game.agent.nodes.scenario_nodes import make_flow_node
from agentic_game.agent.prompts import (
    build_craft_decision_prompt,
    build_craft_response_prompt,
)
from agentic_game.agent.state import CraftState
from agentic_game.application.content_generation import generate_craft_narration
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.application.usecases.craft import CraftItemResult
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.engine.tool_runner import ToolInvoker, execute_craft_tool
from agentic_game.flow.craft import (
    serialize_craft_actions,
)
from agentic_game.scenarios.definitions import CRAFT_SCENARIO
from agentic_game.scenarios.intent import detect_craft_event
from agentic_game.scenarios.spec import ScenarioNode

_craft_flow_node = make_flow_node(
    spec=CRAFT_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 제작 phase에서 허용되지 않은 event입니다.",
)


def make_craft_decision_node(llm: LLMPort):
    """Create a LangGraph node that decides the next craft event."""

    def craft_decision_node(state: CraftState) -> CraftState:
        """Decide the craft event from deterministic intent or LLM output."""
        phase = state.get("phase", CraftPhase.SELECT_RECIPE)
        available_actions = serialize_craft_actions(phase)
        user_text = state.get("human_input") or state.get("user_input", "")
        detected_event = detect_craft_event(phase, user_text)

        if detected_event is not None:
            return {
                "phase": phase,
                "event": detected_event,
                "available_actions": available_actions,
                "reason": "user_input에서 명시적인 제작 행동을 감지했습니다.",
                "next_node": ScenarioNode.FLOW,
            }

        if phase == CraftPhase.SELECT_RECIPE:
            return {
                "phase": phase,
                "event": CraftEvent.CONTINUE,
                "available_actions": available_actions,
                "reason": "제작할 아이템 선택이 필요합니다.",
                "next_node": ScenarioNode.FLOW,
            }

        if phase == CraftPhase.CRAFT:
            return {
                "phase": phase,
                "available_actions": available_actions,
                "reason": "제작할 아이템 선택이 필요합니다.",
                "next_node": ScenarioNode.ASK_USER,
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
            "next_node": ScenarioNode.FLOW,
        }

    return craft_decision_node


def craft_flow_node(state: CraftState) -> CraftState:
    """Advance craft phase according to the selected event."""
    return _craft_flow_node(state)


def craft_hitl_node(state: CraftState) -> CraftState:
    """Ask for a craft recipe when the user has not provided one."""
    human_input = state.get("human_input", "")
    if not detect_craft_event(CraftPhase.CRAFT, human_input):
        return {
            "response": ("HITL 필요: 제작할 아이템을 선택하세요. 가능한 선택: potion / sword"),
            "next_node": ScenarioNode.ASK_USER,
        }

    return {
        "next_node": ScenarioNode.DECISION,
    }


def craft_execute_tool_node(
    state: CraftState,
    *,
    store: StorePort,
    llm: LLMPort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftItemResult],
    random: RandomPort,
) -> CraftState:
    """Invoke the craft tool and persist its raw, LLM, and UI payloads."""
    return execute_craft_tool(
        state=state,
        store=store,
        craft_item_tool=craft_item_tool,
        craft_item=craft_item,
        random=random,
        summarize_tool_result=lambda tool_result: generate_craft_narration(
            llm=llm,
            raw=tool_result.raw,
            llm_payload=tool_result.llm,
        )
        or tool_result.llm["summary"],
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
