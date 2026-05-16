from __future__ import annotations

from agentic_game.agent.nodes.scenario import (
    make_ask_user_node,
    make_decision_node,
    make_flow_node,
    make_hitl_node,
)
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.scenarios import DIALOGUE_SCENARIO
from agentic_game.agent.state import DialogueState
from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.flow.dialogue import serialize_dialogue_actions
from agentic_game.flow.intent import infer_dialogue_event

dialogue_decision_node = make_decision_node(
    default_phase=DialoguePhase.GREETING,
    serialize_actions=serialize_dialogue_actions,
    infer_event=infer_dialogue_event,
    inferred_reason="user_input에서 명시적인 대화 행동을 감지했습니다.",
    fallback_reason="대화 선택이 필요합니다.",
    default_events={
        DialoguePhase.GREETING: (
            DialogueEvent.CONTINUE,
            "NPC와 대화를 시작합니다.",
        ),
    },
)


dialogue_flow_node = make_flow_node(
    spec=DIALOGUE_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 대화 phase에서 허용되지 않은 event입니다.",
)

dialogue_hitl_node = make_hitl_node(
    default_phase=DialoguePhase.CHOICE,
    infer_event=infer_dialogue_event,
    prompt="대화 선택지를 골라 주세요. 가능한 선택: 소문 묻기 / 거래 묻기 / 떠나기",
)


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


dialogue_ask_user_node = make_ask_user_node(
    "대화 선택지를 골라 주세요. 가능한 선택: 소문 묻기 / 거래 묻기 / 감사 / 보상 / 떠나기"
)
