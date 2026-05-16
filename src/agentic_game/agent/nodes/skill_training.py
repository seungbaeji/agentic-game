from __future__ import annotations

from agentic_game.agent.nodes.scenario import make_flow_node
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.scenarios import SKILL_TRAINING_SCENARIO
from agentic_game.agent.state import SkillTrainingState
from agentic_game.domain.skill_training import SkillTrainingPhase
from agentic_game.flow.intent import infer_skill_training_event
from agentic_game.flow.skill_training import serialize_skill_training_actions


def skill_training_decision_node(
    state: SkillTrainingState,
) -> SkillTrainingState:
    """Decide the next skill training event from deterministic intent."""
    phase = state.get("phase", SkillTrainingPhase.SELECT_SKILL)
    available_actions = serialize_skill_training_actions(phase)
    user_text = state.get("human_input") or state.get("user_input", "")
    inferred_event = infer_skill_training_event(phase, user_text)

    if inferred_event is not None:
        return {
            "phase": phase,
            "event": inferred_event,
            "available_actions": available_actions,
            "reason": "user_input에서 명시적인 스킬 훈련 행동을 감지했습니다.",
            "next_node": ScenarioNode.FLOW,
        }

    return {
        "phase": phase,
        "available_actions": available_actions,
        "reason": "훈련할 스킬 또는 행동 선택이 필요합니다.",
        "next_node": ScenarioNode.ASK_USER,
    }


skill_training_flow_node = make_flow_node(
    spec=SKILL_TRAINING_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 스킬 훈련 phase에서 허용되지 않은 event입니다.",
)


def skill_training_hitl_node(
    state: SkillTrainingState,
) -> SkillTrainingState:
    """Ask for skill training input when the graph cannot continue alone."""
    phase = state.get("phase", SkillTrainingPhase.SELECT_SKILL)
    human_input = state.get("human_input", "")

    if infer_skill_training_event(phase, human_input) is None:
        return {
            "response": "훈련 행동을 선택해 주세요. 가능한 선택: 검술 / 연금술 / 훈련 / 레벨 상승",
            "next_node": ScenarioNode.ASK_USER,
        }

    return {
        "next_node": ScenarioNode.DECISION,
    }


def skill_training_execute_node(
    state: SkillTrainingState,
) -> SkillTrainingState:
    """Resolve lightweight skill practice."""
    return {
        "response": "훈련 성과를 확인했습니다. 레벨 상승을 선택할 수 있습니다.",
        "next_node": ScenarioNode.RESPONSE,
    }


def skill_training_response_node(
    state: SkillTrainingState,
) -> SkillTrainingState:
    """Return a deterministic skill training response."""
    phase = state.get("phase")

    if phase == SkillTrainingPhase.TRAIN:
        return {
            "response": "스킬이 선택되었습니다. 이제 훈련을 실행할 수 있습니다.",
        }
    if phase == SkillTrainingPhase.LEVEL_UP:
        return {
            "response": "스킬 레벨이 상승했습니다.",
        }
    if phase == SkillTrainingPhase.COMPLETE:
        return {
            "response": "스킬 훈련을 완료했습니다.",
        }

    existing_response = state.get("response")
    if existing_response:
        return {
            "response": existing_response,
        }

    return {
        "response": "스킬 훈련을 계속 진행합니다.",
    }


def skill_training_ask_user_node(
    state: SkillTrainingState,
) -> SkillTrainingState:
    """Return a user-facing prompt for skill training choices."""
    return {
        "response": "훈련 행동을 선택해 주세요. 가능한 선택: 검술 / 연금술 / 훈련 / 레벨 상승",
    }
