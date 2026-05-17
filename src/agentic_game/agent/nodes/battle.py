from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.decisions import BattleDecision
from agentic_game.agent.nodes.scenario_nodes import make_flow_node
from agentic_game.agent.prompts import (
    build_battle_decision_prompt,
    build_battle_response_prompt,
)
from agentic_game.agent.state import BattleState
from agentic_game.application.content_generation import generate_battle_narration
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.application.usecases.battle import BattleActionResult
from agentic_game.domain.battle import BattlePhase
from agentic_game.engine.tool_runner import ToolInvoker, execute_battle_tool
from agentic_game.flow.battle import (
    serialize_battle_actions,
)
from agentic_game.scenarios.definitions import BATTLE_SCENARIO
from agentic_game.scenarios.intent import detect_battle_event
from agentic_game.scenarios.spec import ScenarioNode

_battle_flow_node = make_flow_node(
    spec=BATTLE_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 전투 phase에서 허용되지 않은 event입니다.",
)


def make_battle_decision_node(llm: LLMPort):
    """Create a LangGraph node that decides the next battle event."""

    def battle_decision_node(state: BattleState) -> BattleState:
        """Decide the battle event from deterministic intent or LLM output."""
        phase = state.get("phase", BattlePhase.PREPARE)
        available_actions = serialize_battle_actions(phase)
        user_text = state.get("human_input") or state.get("user_input", "")
        detected_event = detect_battle_event(phase, user_text)

        if detected_event is not None:
            return {
                "phase": phase,
                "event": detected_event,
                "available_actions": available_actions,
                "reason": "user_input에서 명시적인 전투 행동을 감지했습니다.",
                "next_node": ScenarioNode.FLOW,
            }

        decision = llm.structured_output(
            BattleDecision,
            build_battle_decision_prompt(
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

    return battle_decision_node


def battle_flow_node(state: BattleState) -> BattleState:
    """Advance battle phase according to the selected event."""
    return _battle_flow_node(state)


def battle_hitl_node(state: BattleState) -> BattleState:
    """Ask for human battle input when the graph cannot continue alone."""
    if not state.get("human_input"):
        return {
            "response": ("HITL 필요: 전투 행동을 선택하세요. 가능한 행동: attack / defend / flee"),
            "next_node": ScenarioNode.ASK_USER,
        }

    return {
        "next_node": ScenarioNode.DECISION,
    }


def battle_execute_tool_node(
    state: BattleState,
    *,
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleActionResult],
    random: RandomPort,
) -> BattleState:
    """Invoke the battle tool and persist its raw, LLM, and UI payloads."""
    return execute_battle_tool(
        state=state,
        store=store,
        resolve_battle_tool=resolve_battle_tool,
        resolve_battle_action=resolve_battle_action,
        random=random,
        summarize_tool_result=lambda tool_result: generate_battle_narration(
            llm=llm,
            raw=tool_result.raw,
            llm_payload=tool_result.llm,
        )
        or tool_result.llm["summary"],
    )


def make_battle_response_node(llm: LLMPort):
    """Create a LangGraph node that turns battle state into a response."""

    def battle_response_node(state: BattleState) -> BattleState:
        """Return an existing concrete response or ask the LLM to summarize."""
        existing_response = state.get("response")
        if existing_response:
            return {
                "response": existing_response,
            }

        response = llm.respond(build_battle_response_prompt(state))

        return {
            "response": response,
        }

    return battle_response_node


def battle_ask_user_node(state: BattleState) -> BattleState:
    """Return a user-facing prompt for a valid battle action."""
    return {
        "response": "전투 행동을 선택해 주세요. 가능한 행동: 공격 / 방어 / 도망",
    }
