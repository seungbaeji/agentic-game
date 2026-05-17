from __future__ import annotations

from agentic_game.agent.nodes.scenario_nodes import (
    make_ask_user_node,
    make_decision_node,
    make_flow_node,
    make_hitl_node,
)
from agentic_game.agent.state import QuestState
from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.flow.quest import serialize_quest_actions
from agentic_game.scenarios.definitions import QUEST_SCENARIO
from agentic_game.scenarios.quest import infer_quest_event
from agentic_game.scenarios.spec import ScenarioNode

quest_decision_node = make_decision_node(
    default_phase=QuestPhase.AVAILABLE,
    serialize_actions=serialize_quest_actions,
    infer_event=infer_quest_event,
    inferred_reason="user_input에서 명시적인 퀘스트 행동을 감지했습니다.",
    fallback_reason="퀘스트 행동 선택이 필요합니다.",
    default_events={
        QuestPhase.AVAILABLE: (QuestEvent.ACCEPT, "퀘스트를 수락합니다."),
    },
)


quest_flow_node = make_flow_node(
    spec=QUEST_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 퀘스트 phase에서 허용되지 않은 event입니다.",
)

quest_hitl_node = make_hitl_node(
    default_phase=QuestPhase.ACCEPTED,
    infer_event=infer_quest_event,
    prompt="퀘스트 행동을 선택해 주세요. 가능한 선택: 시작 / 진행 / 완료 / 포기",
)


def quest_execute_node(state: QuestState) -> QuestState:
    """Resolve lightweight quest progress."""
    event = state.get("event")
    if event == QuestEvent.PROGRESS:
        response = "퀘스트 목표를 달성했습니다. 이제 보고할 수 있습니다."
    elif event == QuestEvent.START:
        response = "퀘스트를 계속 진행합니다."
    elif event == QuestEvent.ABANDON:
        response = "퀘스트를 포기했습니다."
    else:
        response = "퀘스트 진행 결과를 정리했습니다."

    return {
        "response": response,
        "next_node": ScenarioNode.RESPONSE,
    }


def quest_response_node(state: QuestState) -> QuestState:
    """Return a deterministic quest response."""
    phase = state.get("phase")
    if phase == QuestPhase.TURN_IN:
        return {
            "response": "퀘스트 목표를 달성했습니다. 보고하고 보상을 받을 수 있습니다.",
        }
    if phase == QuestPhase.COMPLETE:
        return {
            "response": "퀘스트를 완료하고 보상을 받았습니다.",
        }
    if phase == QuestPhase.FAILED:
        return {
            "response": "퀘스트가 실패 상태로 종료되었습니다.",
        }

    existing_response = state.get("response")
    if existing_response:
        return {
            "response": existing_response,
        }

    return {
        "response": "퀘스트를 계속 진행합니다.",
    }


quest_ask_user_node = make_ask_user_node(
    "퀘스트 행동을 선택해 주세요. 가능한 선택: 시작 / 진행 / 완료 / 포기"
)
