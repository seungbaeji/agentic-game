from __future__ import annotations

from agentic_game.agent.nodes.scenario import make_flow_node
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.scenarios import DIALOGUE_SCENARIO
from agentic_game.agent.state import DialogueState
from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.flow.dialogue import serialize_dialogue_actions
from agentic_game.flow.intent import infer_dialogue_event


def dialogue_decision_node(state: DialogueState) -> DialogueState:
    """Decide the next dialogue event from deterministic intent."""
    phase = state.get("phase", DialoguePhase.GREETING)
    available_actions = serialize_dialogue_actions(phase)
    user_text = state.get("human_input") or state.get("user_input", "")
    inferred_event = infer_dialogue_event(phase, user_text)

    if inferred_event is not None:
        return {
            "phase": phase,
            "event": inferred_event,
            "available_actions": available_actions,
            "reason": "user_input에서 명시적인 대화 행동을 감지했습니다.",
            "next_node": ScenarioNode.FLOW,
        }

    if phase == DialoguePhase.GREETING:
        return {
            "phase": phase,
            "event": DialogueEvent.CONTINUE,
            "available_actions": available_actions,
            "reason": "NPC와 대화를 시작합니다.",
            "next_node": ScenarioNode.FLOW,
        }

    return {
        "phase": phase,
        "available_actions": available_actions,
        "reason": "대화 선택이 필요합니다.",
        "next_node": ScenarioNode.ASK_USER,
    }


dialogue_flow_node = make_flow_node(
    spec=DIALOGUE_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 대화 phase에서 허용되지 않은 event입니다.",
)


def dialogue_hitl_node(state: DialogueState) -> DialogueState:
    """Ask for dialogue input when the graph cannot continue alone."""
    phase = state.get("phase", DialoguePhase.CHOICE)
    human_input = state.get("human_input", "")

    if infer_dialogue_event(phase, human_input) is None:
        return {
            "response": "대화 선택지를 골라 주세요. 가능한 선택: 소문 묻기 / 거래 묻기 / 떠나기",
            "next_node": ScenarioNode.ASK_USER,
        }

    return {
        "next_node": ScenarioNode.DECISION,
    }


def dialogue_execute_node(state: DialogueState) -> DialogueState:
    """No-op execute node for dialogue graphs."""
    return {
        "next_node": ScenarioNode.RESPONSE,
    }


def dialogue_response_node(state: DialogueState) -> DialogueState:
    """Return a deterministic NPC dialogue response."""
    phase = state.get("phase")
    event = state.get("event")

    if phase == DialoguePhase.REACT and event == DialogueEvent.ASK_RUMOR:
        return {
            "response": "NPC가 오래된 유적에 대한 소문을 들려줬습니다.",
        }
    if phase == DialoguePhase.REACT and event == DialogueEvent.ASK_TRADE:
        return {
            "response": "NPC가 근처 상인을 소개해 줬습니다.",
        }
    if phase == DialoguePhase.REWARD:
        return {
            "response": "NPC가 감사의 표시로 작은 보상을 준비했습니다.",
        }
    if phase == DialoguePhase.END:
        return {
            "response": "NPC와의 대화를 마쳤습니다.",
        }

    existing_response = state.get("response")
    if existing_response:
        return {
            "response": existing_response,
        }

    return {
        "response": "NPC와 대화를 이어갑니다.",
    }


def dialogue_ask_user_node(state: DialogueState) -> DialogueState:
    """Return a user-facing prompt for dialogue choices."""
    return {
        "response": "대화 선택지를 골라 주세요. 가능한 선택: 소문 묻기 / 거래 묻기 / 감사 / 보상 / 떠나기",
    }
