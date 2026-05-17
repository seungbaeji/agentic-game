from __future__ import annotations

from agentic_game.agent.nodes.scenario_nodes import (
    make_ask_user_node,
    make_decision_node,
    make_flow_node,
    make_hitl_node,
)
from agentic_game.agent.state import SkillTrainingState
from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.ports import StorePort
from agentic_game.application.usecases.skill_training import (
    level_up_trained_skill,
    practice_skill,
    skill_id_from_event,
)
from agentic_game.domain.skill_training import SkillTrainingPhase
from agentic_game.flow.skill_training import serialize_skill_training_actions
from agentic_game.scenarios.definitions import SKILL_TRAINING_SCENARIO
from agentic_game.scenarios.skill_training import infer_skill_training_event
from agentic_game.scenarios.spec import ScenarioNode

skill_training_decision_node = make_decision_node(
    default_phase=SkillTrainingPhase.SELECT_SKILL,
    serialize_actions=serialize_skill_training_actions,
    infer_event=infer_skill_training_event,
    inferred_reason="user_input에서 명시적인 스킬 훈련 행동을 감지했습니다.",
    fallback_reason="훈련할 스킬 또는 행동 선택이 필요합니다.",
)


skill_training_flow_node = make_flow_node(
    spec=SKILL_TRAINING_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 스킬 훈련 phase에서 허용되지 않은 event입니다.",
)

skill_training_hitl_node = make_hitl_node(
    default_phase=SkillTrainingPhase.SELECT_SKILL,
    infer_event=infer_skill_training_event,
    prompt="훈련 행동을 선택해 주세요. 가능한 선택: 검술 / 연금술 / 훈련 / 레벨 상승",
)


def make_skill_training_execute_node(store: StorePort):
    """Create a node that stores skill practice progress."""

    def skill_training_execute_node(
        state: SkillTrainingState,
    ) -> SkillTrainingState:
        """Resolve lightweight skill practice and persist exp."""
        selected_skill = state.get("selected_skill") or "swordsmanship"
        practice_skill(
            skill_id=selected_skill,
            game_state=GameStateRepository(store),
        )
        return {
            "response": "훈련 성과를 확인했습니다. 레벨 상승을 선택할 수 있습니다.",
            "next_node": ScenarioNode.RESPONSE,
        }

    return skill_training_execute_node


def make_skill_training_response_node(store: StorePort):
    """Create a node that stores skill level-up progress."""

    def skill_training_response_node(
        state: SkillTrainingState,
    ) -> SkillTrainingState:
        """Return a deterministic skill training response."""
        phase = state.get("phase")

        if phase == SkillTrainingPhase.TRAIN:
            selected_skill = skill_id_from_event(state.get("event"))
            update: SkillTrainingState = {
                "response": "스킬이 선택되었습니다. 이제 훈련을 실행할 수 있습니다.",
            }
            if selected_skill is not None:
                update["selected_skill"] = selected_skill
            return update

        if phase == SkillTrainingPhase.LEVEL_UP:
            selected_skill = state.get("selected_skill") or "swordsmanship"
            level_up_trained_skill(
                skill_id=selected_skill,
                game_state=GameStateRepository(store),
            )
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

    return skill_training_response_node


skill_training_ask_user_node = make_ask_user_node(
    "훈련 행동을 선택해 주세요. 가능한 선택: 검술 / 연금술 / 훈련 / 레벨 상승"
)
