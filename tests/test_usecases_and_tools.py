from __future__ import annotations

from langgraph.store.memory import InMemoryStore

from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.usecases import (
    craft_item,
    craft_item_and_store_reward,
    exchange_item,
    level_up_trained_skill,
    practice_skill,
    resolve_battle_action,
    resolve_battle_action_and_store_player,
)
from agentic_game.domain.battle import BattleOutcome
from agentic_game.outbound.store import LangGraphStoreAdapter
from agentic_game.tools import craft_item_tool, resolve_battle_tool
from agentic_game.tools.types import ToolResult
from tests.fakes import FixedRandom


def test_resolve_battle_action_uses_random_port() -> None:
    result = resolve_battle_action("attack", random=FixedRandom(d20=[18], damage=[11]))

    assert result.outcome == BattleOutcome.CRITICAL_HIT
    assert result.damage == 11


def test_resolve_battle_action_and_store_player_adds_exp() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    result = resolve_battle_action_and_store_player(
        "attack",
        random=FixedRandom(d20=[18], damage=[11]),
        game_state=game_state,
    )

    player = game_state.load_player()

    assert result.player_delta is not None
    assert result.player_delta.exp_gain == 20
    assert player.hp == 100
    assert player.exp == 20


def test_craft_item_uses_random_port() -> None:
    result = craft_item("potion", random=FixedRandom(d20=[19]))

    assert result.success is True
    assert result.bonus is True


def test_craft_item_and_store_reward_adds_successful_item_to_inventory() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    result = craft_item_and_store_reward(
        "potion",
        random=FixedRandom(d20=[19]),
        game_state=game_state,
    )

    inventory = game_state.load_inventory()

    assert result.success is True
    assert result.inventory_delta is not None
    assert result.inventory_delta.item_id == "healing_potion"
    assert inventory.items[0].item_id == "healing_potion"
    assert inventory.items[0].quantity == 1


def test_skill_training_usecases_update_skill_book() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    practice_result = practice_skill(
        skill_id="alchemy",
        game_state=game_state,
    )
    level_up_result = level_up_trained_skill(
        skill_id="alchemy",
        game_state=game_state,
    )

    skill_book = game_state.load_skills()

    assert practice_result.skill_book.skills[0].skill_id == "alchemy"
    assert practice_result.skill_book.skills[0].level == 1
    assert practice_result.skill_book.skills[0].exp == 10
    assert level_up_result.skill_book.skills[0].level == 2
    assert skill_book.skills[0].level == 2
    assert skill_book.skills[0].exp == 0


def test_trade_exchange_item_updates_player_gold_and_inventory() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    result = exchange_item(game_state=game_state)

    player = game_state.load_player()
    inventory = game_state.load_inventory()

    assert result.item_id == "travel_ration"
    assert result.price == 15
    assert player.gold == 85
    assert inventory.items[0].item_id == "travel_ration"
    assert inventory.items[0].quantity == 1


def test_tool_schema_hides_injected_dependencies() -> None:
    assert resolve_battle_tool.args == {"action": {"title": "Action", "type": "string"}}
    assert craft_item_tool.args == {"recipe": {"title": "Recipe", "type": "string"}}


def test_resolve_battle_tool_returns_internal_dataclass() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    result = resolve_battle_tool.invoke(
        {
            "action": "attack",
            "resolve_battle_action": resolve_battle_action_and_store_player,
            "random": FixedRandom(d20=[12], damage=[8]),
            "game_state": GameStateRepository(store),
        }
    )

    assert isinstance(result, ToolResult)
    assert result.raw["outcome"] == BattleOutcome.HIT.value
    assert result.raw["damage"] == 8
    assert result.raw["player_delta"] == {"hp_change": 0, "exp_gain": 10}
    assert result.metadata["system_event"] == "tool.battle.resolve.completed"


def test_craft_item_tool_returns_internal_dataclass() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    result = craft_item_tool.invoke(
        {
            "recipe": "potion",
            "craft_item": craft_item_and_store_reward,
            "random": FixedRandom(d20=[6]),
            "game_state": GameStateRepository(store),
        }
    )

    assert isinstance(result, ToolResult)
    assert result.raw["success"] is False
    assert result.raw["item_name"] == "healing_potion"
    assert result.raw["inventory_delta"] is None
    assert result.metadata["system_event"] == "tool.craft.completed"
