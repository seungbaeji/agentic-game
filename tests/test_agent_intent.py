from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.domain.skill_training import SkillTrainingEvent, SkillTrainingPhase
from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.models import SubgraphName
from agentic_game.scenarios.battle import infer_battle_event
from agentic_game.scenarios.craft import infer_craft_event
from agentic_game.scenarios.dialogue import infer_dialogue_event
from agentic_game.scenarios.exploration import infer_exploration_event
from agentic_game.scenarios.quest import infer_quest_event
from agentic_game.scenarios.router import infer_parent_subgraph, is_capability_question
from agentic_game.scenarios.skill_training import infer_skill_training_event
from agentic_game.scenarios.trade import infer_trade_event


def test_infer_battle_event_from_direct_prepare_input() -> None:
    assert infer_battle_event(BattlePhase.PREPARE, "몬스터랑 전투를 시작하고 공격할게") == BattleEvent.ATTACK


def test_infer_battle_event_respects_available_phase_actions() -> None:
    assert infer_battle_event(BattlePhase.RESOLVE, "다시 공격할게") is None


def test_infer_craft_event_from_direct_select_recipe_input() -> None:
    assert infer_craft_event(CraftPhase.SELECT_RECIPE, "포션을 제작하고 싶어") == CraftEvent.CRAFT_POTION


def test_infer_craft_event_does_not_guess_recipe_from_vague_craft_intent() -> None:
    assert infer_craft_event(CraftPhase.SELECT_RECIPE, "제작하고 싶어") is None


def test_infer_craft_event_respects_available_phase_actions() -> None:
    assert infer_craft_event(CraftPhase.RESULT, "검 만들래") is None


def test_infer_exploration_event_from_path_choice() -> None:
    assert (
        infer_exploration_event(ExplorationPhase.CHOOSE_PATH, "숲길로 갈래")
        == ExplorationEvent.TAKE_FOREST
    )


def test_infer_exploration_event_respects_available_phase_actions() -> None:
    assert infer_exploration_event(ExplorationPhase.START, "숲길로 갈래") is None


def test_infer_trade_event_from_price_offer() -> None:
    assert infer_trade_event(TradePhase.NEGOTIATE, "가격을 제안할게") == TradeEvent.OFFER


def test_infer_trade_event_respects_available_phase_actions() -> None:
    assert infer_trade_event(TradePhase.BROWSE, "수락할게") is None


def test_infer_quest_event_from_progress_input() -> None:
    assert infer_quest_event(QuestPhase.IN_PROGRESS, "목표를 달성했어") == QuestEvent.PROGRESS


def test_infer_quest_event_respects_available_phase_actions() -> None:
    assert infer_quest_event(QuestPhase.AVAILABLE, "완료할게") is None


def test_infer_dialogue_event_from_rumor_input() -> None:
    assert infer_dialogue_event(DialoguePhase.CHOICE, "소문을 물어볼게") == DialogueEvent.ASK_RUMOR


def test_infer_dialogue_event_respects_available_phase_actions() -> None:
    assert infer_dialogue_event(DialoguePhase.GREETING, "소문을 물어볼게") is None


def test_infer_skill_training_event_from_skill_selection() -> None:
    assert (
        infer_skill_training_event(SkillTrainingPhase.SELECT_SKILL, "검술을 훈련할게")
        == SkillTrainingEvent.SELECT_SWORDSMANSHIP
    )


def test_infer_skill_training_event_respects_available_phase_actions() -> None:
    assert infer_skill_training_event(SkillTrainingPhase.SELECT_SKILL, "레벨 올릴게") is None


def test_infer_parent_subgraph_from_battle_intent() -> None:
    assert infer_parent_subgraph("몬스터를 공격할게") == SubgraphName.BATTLE


def test_infer_parent_subgraph_from_craft_intent() -> None:
    assert infer_parent_subgraph("제작하고 싶어") == SubgraphName.CRAFT


def test_infer_parent_subgraph_from_exploration_intent() -> None:
    assert infer_parent_subgraph("숲을 탐험하고 싶어") == SubgraphName.EXPLORATION


def test_infer_parent_subgraph_from_trade_intent() -> None:
    assert infer_parent_subgraph("상인과 거래하고 싶어") == SubgraphName.TRADE


def test_infer_parent_subgraph_from_quest_intent() -> None:
    assert infer_parent_subgraph("퀘스트를 수락하고 싶어") == SubgraphName.QUEST


def test_infer_parent_subgraph_from_dialogue_intent() -> None:
    assert infer_parent_subgraph("NPC와 대화하고 싶어") == SubgraphName.DIALOGUE


def test_infer_parent_subgraph_from_skill_training_intent() -> None:
    assert infer_parent_subgraph("검술을 훈련하고 싶어") == SubgraphName.SKILL_TRAINING


def test_infer_parent_subgraph_returns_none_for_capability_question() -> None:
    assert infer_parent_subgraph("어떤걸 할 수 있어?") is None


def test_capability_question_is_detected_without_llm() -> None:
    assert is_capability_question("어떤걸 할 수 있어?") is True
