from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.domain.skill_training import SkillTrainingEvent, SkillTrainingPhase
from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.battle import resolve_battle_transition, serialize_battle_actions
from agentic_game.flow.craft import resolve_craft_transition, serialize_craft_actions
from agentic_game.flow.dialogue import (
    resolve_dialogue_transition,
    serialize_dialogue_actions,
)
from agentic_game.flow.exploration import (
    resolve_exploration_transition,
    serialize_exploration_actions,
)
from agentic_game.flow.quest import resolve_quest_transition, serialize_quest_actions
from agentic_game.flow.skill_training import (
    resolve_skill_training_transition,
    serialize_skill_training_actions,
)
from agentic_game.flow.trade import resolve_trade_transition, serialize_trade_actions


def test_battle_flow_exposes_only_current_phase_actions() -> None:
    actions = serialize_battle_actions(BattlePhase.ACTION)

    assert {action["event"] for action in actions} == {
        BattleEvent.ATTACK.value,
        BattleEvent.DEFEND.value,
        BattleEvent.FLEE.value,
    }
    attack = next(action for action in actions if action["event"] == BattleEvent.ATTACK)
    assert attack["tool_name"] == "resolve_battle_tool"
    assert attack["risk"] == "state_change"


def test_battle_flow_resolves_allowed_transition() -> None:
    rule = resolve_battle_transition(BattlePhase.ACTION, BattleEvent.ATTACK)

    assert rule is not None
    assert rule.to_phase == BattlePhase.RESOLVE


def test_battle_flow_rejects_unavailable_transition() -> None:
    assert resolve_battle_transition(BattlePhase.PREPARE, BattleEvent.RETRY) is None


def test_battle_flow_allows_direct_action_from_prepare() -> None:
    rule = resolve_battle_transition(BattlePhase.PREPARE, BattleEvent.ATTACK)

    assert rule is not None
    assert rule.to_phase == BattlePhase.RESOLVE


def test_craft_flow_exposes_only_current_phase_actions() -> None:
    actions = serialize_craft_actions(CraftPhase.CRAFT)

    assert {action["event"] for action in actions} == {
        CraftEvent.CRAFT_CONSUMABLE.value,
        CraftEvent.CRAFT_WEAPON.value,
        CraftEvent.CRAFT_ARMOR.value,
        CraftEvent.CRAFT_ACCESSORY.value,
        CraftEvent.CRAFT_TOOL.value,
        CraftEvent.CRAFT_MATERIAL.value,
    }
    consumable = next(
        action for action in actions if action["event"] == CraftEvent.CRAFT_CONSUMABLE
    )
    assert consumable["tool_name"] == "craft_item_tool"
    assert consumable["state_effect"] == (
        "consumable item can be added to inventory on success."
    )


def test_craft_flow_resolves_allowed_transition() -> None:
    rule = resolve_craft_transition(CraftPhase.CRAFT, CraftEvent.CRAFT_WEAPON)

    assert rule is not None
    assert rule.to_phase == CraftPhase.RESULT


def test_craft_flow_rejects_unavailable_transition() -> None:
    assert resolve_craft_transition(CraftPhase.SELECT_RECIPE, CraftEvent.RETRY) is None


def test_craft_flow_allows_direct_category_from_select_recipe() -> None:
    rule = resolve_craft_transition(
        CraftPhase.SELECT_RECIPE,
        CraftEvent.CRAFT_CONSUMABLE,
    )

    assert rule is not None
    assert rule.to_phase == CraftPhase.RESULT


def test_exploration_flow_exposes_only_current_phase_actions() -> None:
    actions = serialize_exploration_actions(ExplorationPhase.CHOOSE_PATH)

    assert {action["event"] for action in actions} == {
        ExplorationEvent.TAKE_FOREST.value,
        ExplorationEvent.TAKE_RUINS.value,
    }


def test_exploration_flow_resolves_branching_path() -> None:
    forest_rule = resolve_exploration_transition(
        ExplorationPhase.CHOOSE_PATH,
        ExplorationEvent.TAKE_FOREST,
    )
    ruins_rule = resolve_exploration_transition(
        ExplorationPhase.CHOOSE_PATH,
        ExplorationEvent.TAKE_RUINS,
    )

    assert forest_rule is not None
    assert forest_rule.to_phase == ExplorationPhase.ENCOUNTER
    assert ruins_rule is not None
    assert ruins_rule.to_phase == ExplorationPhase.DISCOVER


def test_exploration_flow_rejects_unavailable_transition() -> None:
    assert (
        resolve_exploration_transition(
            ExplorationPhase.START,
            ExplorationEvent.INSPECT,
        )
        is None
    )


def test_quest_flow_exposes_failure_and_progress_actions() -> None:
    actions = serialize_quest_actions(QuestPhase.IN_PROGRESS)

    assert {action["event"] for action in actions} == {
        QuestEvent.PROGRESS.value,
        QuestEvent.ABANDON.value,
        QuestEvent.FAIL.value,
    }


def test_quest_flow_resolves_success_path() -> None:
    rule = resolve_quest_transition(QuestPhase.IN_PROGRESS, QuestEvent.PROGRESS)

    assert rule is not None
    assert rule.to_phase == QuestPhase.TURN_IN


def test_quest_flow_resolves_failure_path() -> None:
    abandon_rule = resolve_quest_transition(QuestPhase.IN_PROGRESS, QuestEvent.ABANDON)
    fail_rule = resolve_quest_transition(QuestPhase.IN_PROGRESS, QuestEvent.FAIL)

    assert abandon_rule is not None
    assert abandon_rule.to_phase == QuestPhase.FAILED
    assert fail_rule is not None
    assert fail_rule.to_phase == QuestPhase.FAILED


def test_trade_flow_exposes_confirm_actions() -> None:
    actions = serialize_trade_actions(TradePhase.CONFIRM)

    assert {action["event"] for action in actions} == {
        TradeEvent.ACCEPT_PRICE.value,
        TradeEvent.DECLINE_PRICE.value,
        TradeEvent.CANCEL.value,
    }
    accept = next(
        action for action in actions if action["event"] == TradeEvent.ACCEPT_PRICE
    )
    assert accept["tool_name"] == "exchange_item_tool"
    assert accept["risk"] == "state_change"


def test_trade_flow_resolves_exchange_path() -> None:
    rule = resolve_trade_transition(TradePhase.CONFIRM, TradeEvent.ACCEPT_PRICE)

    assert rule is not None
    assert rule.to_phase == TradePhase.EXCHANGE


def test_trade_flow_resolves_cancel_path() -> None:
    rule = resolve_trade_transition(TradePhase.NEGOTIATE, TradeEvent.CANCEL)

    assert rule is not None
    assert rule.to_phase == TradePhase.CANCELLED


def test_dialogue_flow_exposes_choice_actions() -> None:
    actions = serialize_dialogue_actions(DialoguePhase.CHOICE)

    assert {action["event"] for action in actions} == {
        DialogueEvent.ASK_RUMOR.value,
        DialogueEvent.ASK_TRADE.value,
        DialogueEvent.LEAVE.value,
    }


def test_dialogue_flow_resolves_reaction_path() -> None:
    rule = resolve_dialogue_transition(DialoguePhase.CHOICE, DialogueEvent.ASK_RUMOR)

    assert rule is not None
    assert rule.to_phase == DialoguePhase.REACT


def test_dialogue_flow_resolves_reward_path() -> None:
    rule = resolve_dialogue_transition(DialoguePhase.REACT, DialogueEvent.THANK)

    assert rule is not None
    assert rule.to_phase == DialoguePhase.REWARD


def test_skill_training_flow_exposes_skill_selection_actions() -> None:
    actions = serialize_skill_training_actions(SkillTrainingPhase.SELECT_SKILL)

    assert {action["event"] for action in actions} == {
        SkillTrainingEvent.SELECT_SWORDSMANSHIP.value,
        SkillTrainingEvent.SELECT_ALCHEMY.value,
    }


def test_skill_training_flow_resolves_training_execution() -> None:
    rule = resolve_skill_training_transition(
        SkillTrainingPhase.TRAIN,
        SkillTrainingEvent.PRACTICE,
    )

    assert rule is not None
    assert rule.to_phase == SkillTrainingPhase.RESOLVE


def test_skill_training_flow_resolves_retry_and_level_up_paths() -> None:
    retry_rule = resolve_skill_training_transition(
        SkillTrainingPhase.RESOLVE,
        SkillTrainingEvent.RETRY,
    )
    level_up_rule = resolve_skill_training_transition(
        SkillTrainingPhase.RESOLVE,
        SkillTrainingEvent.LEVEL_UP,
    )

    assert retry_rule is not None
    assert retry_rule.to_phase == SkillTrainingPhase.TRAIN
    assert level_up_rule is not None
    assert level_up_rule.to_phase == SkillTrainingPhase.LEVEL_UP
