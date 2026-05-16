from __future__ import annotations

from agentic_game.agent.nodes.scenario import (
    make_ask_user_node,
    make_flow_node,
    make_hitl_node,
)
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.scenarios import EXPLORATION_SCENARIO
from agentic_game.agent.state import ExplorationState
from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.flow.exploration import serialize_exploration_actions
from agentic_game.flow.intent import infer_exploration_event


def exploration_decision_node(state: ExplorationState) -> ExplorationState:
    """Decide the next exploration event from deterministic intent."""
    phase = state.get("phase", ExplorationPhase.START)
    available_actions = serialize_exploration_actions(phase)
    user_text = state.get("human_input") or state.get("user_input", "")
    inferred_event = infer_exploration_event(phase, user_text)

    if inferred_event is not None:
        return {
            "phase": phase,
            "event": inferred_event,
            "available_actions": available_actions,
            "reason": "user_input에서 명시적인 탐험 행동을 감지했습니다.",
            "next_node": ScenarioNode.FLOW,
        }

    if phase == ExplorationPhase.START:
        return {
            "phase": phase,
            "event": ExplorationEvent.CONTINUE,
            "available_actions": available_actions,
            "reason": "탐험을 시작합니다.",
            "next_node": ScenarioNode.FLOW,
        }

    return {
        "phase": phase,
        "available_actions": available_actions,
        "reason": "탐험 경로나 행동 선택이 필요합니다.",
        "next_node": ScenarioNode.ASK_USER,
    }


exploration_flow_node = make_flow_node(
    spec=EXPLORATION_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 탐험 phase에서 허용되지 않은 event입니다.",
)

exploration_hitl_node = make_hitl_node(
    default_phase=ExplorationPhase.CHOOSE_PATH,
    infer_event=infer_exploration_event,
    prompt="탐험 경로를 선택해 주세요. 가능한 선택: 숲길 / 유적",
)


def exploration_execute_node(state: ExplorationState) -> ExplorationState:
    """Resolve a lightweight exploration encounter."""
    event = state.get("event")
    if event == ExplorationEvent.TAKE_FOREST:
        response = "숲길에서 낯선 흔적을 발견했습니다. 조사하거나 후퇴할 수 있습니다."
    else:
        response = "탐험 중 새로운 단서를 발견했습니다."

    return {
        "response": response,
        "next_node": ScenarioNode.RESPONSE,
    }


def exploration_response_node(state: ExplorationState) -> ExplorationState:
    """Return a deterministic exploration response."""
    existing_response = state.get("response")
    if existing_response:
        return {
            "response": existing_response,
        }

    phase = state.get("phase")
    if phase == ExplorationPhase.DISCOVER:
        return {
            "response": "탐험에서 유용한 단서를 발견했습니다.",
        }

    if phase == ExplorationPhase.COMPLETE:
        return {
            "response": "탐험을 마쳤습니다.",
        }

    return {
        "response": "탐험을 계속 진행합니다.",
    }


exploration_ask_user_node = make_ask_user_node(
    "탐험 행동을 선택해 주세요. 가능한 선택: 숲길 / 유적 / 조사 / 후퇴"
)
