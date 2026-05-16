from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.flow.intent import (
    infer_battle_event,
    infer_craft_event,
    infer_parent_subgraph,
    is_capability_question,
)
from agentic_game.flow.models import SubgraphName


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


def test_infer_parent_subgraph_from_battle_intent() -> None:
    assert infer_parent_subgraph("몬스터를 공격할게") == SubgraphName.BATTLE


def test_infer_parent_subgraph_from_craft_intent() -> None:
    assert infer_parent_subgraph("제작하고 싶어") == SubgraphName.CRAFT


def test_infer_parent_subgraph_returns_none_for_capability_question() -> None:
    assert infer_parent_subgraph("어떤걸 할 수 있어?") is None


def test_capability_question_is_detected_without_llm() -> None:
    assert is_capability_question("어떤걸 할 수 있어?") is True
