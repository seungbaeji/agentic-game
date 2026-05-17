from __future__ import annotations

from agentic_game.agent.decisions import DialogueDecision
from agentic_game.agent.nodes.scenario_nodes import (
    make_ask_user_node,
    make_flow_node,
    make_hitl_node,
)
from agentic_game.agent.prompts import (
    build_dialogue_decision_prompt,
    build_dialogue_response_prompt,
)
from agentic_game.agent.state import DialogueState
from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.ports import LLMPort, StorePort
from agentic_game.application.usecases.dialogue import remember_dialogue_event
from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.flow.dialogue import serialize_dialogue_actions
from agentic_game.scenarios.definitions import DIALOGUE_SCENARIO
from agentic_game.scenarios.intent import detect_dialogue_event
from agentic_game.scenarios.spec import ScenarioNode


def make_dialogue_decision_node(llm: LLMPort):
    """Create a dialogue decision node that uses LLM for non-command input."""

    def dialogue_decision_node(state: DialogueState) -> DialogueState:
        """Classify dialogue input as an action or direct conversational response."""
        phase = state.get("phase", DialoguePhase.GREETING)
        available_actions = serialize_dialogue_actions(phase)
        user_text = state.get("human_input") or state.get("user_input", "")
        detected_event = detect_dialogue_event(phase, user_text)

        if detected_event is not None:
            return {
                "phase": phase,
                "event": detected_event,
                "input_intent": "action",
                "available_actions": available_actions,
                "reason": "user_input에서 명시적인 대화 행동을 감지했습니다.",
                "next_node": ScenarioNode.FLOW,
            }

        if phase == DialoguePhase.GREETING:
            return {
                "phase": phase,
                "event": DialogueEvent.CONTINUE,
                "input_intent": "action",
                "available_actions": available_actions,
                "reason": "NPC와 대화를 시작합니다.",
                "next_node": ScenarioNode.FLOW,
            }

        decision = llm.structured_output(
            DialogueDecision,
            build_dialogue_decision_prompt(
                phase=phase,
                available_actions=available_actions,
                user_text=user_text,
                last_topic=state.get("last_topic"),
                last_response=state.get("response"),
            ),
        )

        if decision.intent == "action" and decision.event is not None:
            available_events = {action["event"] for action in available_actions}
            if decision.event.value in available_events:
                return {
                    "phase": phase,
                    "event": decision.event,
                    "input_intent": "action",
                    "available_actions": available_actions,
                    "reason": decision.reason,
                    "next_node": ScenarioNode.FLOW,
                }

            return {
                "phase": phase,
                "input_intent": "clarify",
                "available_actions": available_actions,
                "response": "지금 대화에서 가능한 선택을 골라 주세요.",
                "reason": "LLM이 현재 phase에서 허용되지 않은 event를 선택했습니다.",
                "next_node": ScenarioNode.RESPONSE,
            }

        return {
            "phase": phase,
            "input_intent": decision.intent,
            "available_actions": available_actions,
            "response": decision.response or "조금 더 구체적으로 말해 주세요.",
            "reason": decision.reason,
            "next_node": ScenarioNode.RESPONSE,
        }

    return dialogue_decision_node


dialogue_flow_node = make_flow_node(
    spec=DIALOGUE_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 대화 phase에서 허용되지 않은 event입니다.",
)

dialogue_hitl_node = make_hitl_node(
    default_phase=DialoguePhase.CHOICE,
    detect_event=detect_dialogue_event,
    prompt="대화 선택지를 골라 주세요. 가능한 선택: 소문 묻기 / 거래 묻기 / 떠나기",
)


def dialogue_execute_node(state: DialogueState) -> DialogueState:
    """No-op execute node for dialogue graphs."""
    return {
        "next_node": ScenarioNode.RESPONSE,
    }


def make_dialogue_response_node(store: StorePort):
    """Create a node that stores deterministic NPC dialogue memory."""

    def dialogue_response_node(state: DialogueState) -> DialogueState:
        """Return a deterministic NPC dialogue response."""
        phase = state.get("phase")
        event = state.get("event")
        existing_response = state.get("response")

        if state.get("input_intent") in {"question", "clarify", "smalltalk"}:
            return {
                "response": existing_response or "대화를 이어가려면 조금 더 구체적으로 말해 주세요.",
            }

        if phase == DialoguePhase.REACT and event == DialogueEvent.ASK_RUMOR:
            remember_dialogue_event(
                event=event,
                game_state=GameStateRepository(store),
            )
            return {
                "last_topic": "old_ruins_rumor",
                "response": (
                    "NPC는 북쪽의 오래된 유적에서 밤마다 푸른 빛이 새어 나오고, "
                    "가끔 낮은 종소리가 들린다는 소문을 들려줬습니다."
                ),
            }
        if phase == DialoguePhase.REACT and event == DialogueEvent.ASK_TRADE:
            remember_dialogue_event(
                event=event,
                game_state=GameStateRepository(store),
            )
            return {
                "last_topic": "merchant_intro",
                "response": "NPC가 근처 상인을 소개해 줬습니다.",
            }
        if phase == DialoguePhase.REWARD:
            remember_dialogue_event(
                event=event,
                game_state=GameStateRepository(store),
            )
            return {
                "response": "NPC가 감사의 표시로 작은 보상을 준비했습니다.",
            }
        if phase == DialoguePhase.END:
            return {
                "response": "NPC와의 대화를 마쳤습니다.",
            }

        if existing_response:
            return {
                "response": existing_response,
            }

        return {
            "response": "NPC와 대화를 이어갑니다.",
        }

    return dialogue_response_node


def make_llm_dialogue_response_node(store: StorePort, llm: LLMPort):
    """Create a dialogue response node that lets LLM polish direct responses."""
    deterministic_response_node = make_dialogue_response_node(store)

    def dialogue_response_node(state: DialogueState) -> DialogueState:
        response_state = deterministic_response_node(state)
        if state.get("input_intent") == "action":
            return response_state

        polished_response = llm.respond(
            build_dialogue_response_prompt(
                {
                    **state,
                    **response_state,
                }
            )
        )
        if not polished_response:
            return response_state

        return {
            **response_state,
            "response": polished_response,
        }

    return dialogue_response_node


dialogue_ask_user_node = make_ask_user_node(
    "대화 선택지를 골라 주세요. 가능한 선택: 소문 묻기 / 거래 묻기 / 감사 / 보상 / 떠나기"
)
