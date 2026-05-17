from __future__ import annotations

from langgraph.store.memory import InMemoryStore

from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.usecases import (
    complete_quest,
    craft_item,
    craft_item_and_store_reward,
    discover_exploration_location,
    exchange_item,
    level_up_trained_skill,
    mark_quest_progress,
    practice_skill,
    remember_dialogue_event,
    resolve_battle_action,
    resolve_battle_action_and_store_player,
)
from agentic_game.domain.battle import BattleOutcome
from agentic_game.domain.craft import CraftCategory
from agentic_game.domain.dialogue import DialogueEvent
from agentic_game.domain.exploration import ExplorationEvent
from agentic_game.outbound.store import LangGraphStoreAdapter
from agentic_game.tools import craft_item_tool, exchange_item_tool, resolve_battle_tool
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
    result = craft_item(CraftCategory.CONSUMABLE, random=FixedRandom(d20=[19]))

    assert result.success is True
    assert result.bonus is True


def test_craft_item_and_store_reward_adds_successful_item_to_inventory() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    result = craft_item_and_store_reward(
        CraftCategory.CONSUMABLE,
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


def test_quest_usecases_update_quest_log_and_player_rewards() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    progress_result = mark_quest_progress(game_state=game_state)
    complete_result = complete_quest(game_state=game_state)

    quest_log = game_state.load_quests()
    player = game_state.load_player()

    assert progress_result.quest_log.quests[0].status == "ready_to_turn_in"
    assert complete_result.quest_log.quests[0].status == "complete"
    assert quest_log.quests[0].quest_id == "old_ruins"
    assert quest_log.quests[0].progress == 100
    assert player.exp == 25
    assert player.gold == 120


def test_exploration_usecase_updates_world_state() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    result = discover_exploration_location(
        event=ExplorationEvent.TAKE_FOREST,
        game_state=game_state,
    )

    world = game_state.load_world()

    assert result.location_id == "forest_path"
    assert world.current_location == "forest_path"
    assert world.discovered_locations == ("forest_path",)


def test_dialogue_usecase_updates_npc_memory() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    game_state = GameStateRepository(store)

    remember_dialogue_event(
        event=DialogueEvent.ASK_RUMOR,
        game_state=game_state,
    )
    remember_dialogue_event(
        event=DialogueEvent.THANK,
        game_state=game_state,
    )

    npc_memory = game_state.load_npcs()

    assert npc_memory.npcs[0].npc_id == "village_elder"
    assert npc_memory.npcs[0].relation == 1
    assert npc_memory.npcs[0].memories == (
        "old_ruins_rumor",
        "received_thanks",
    )


def test_tool_schema_hides_injected_dependencies() -> None:
    assert resolve_battle_tool.args == {"action": {"title": "Action", "type": "string"}}
    assert craft_item_tool.args == {
        "category": {"title": "Category", "type": "string"},
        "item_name": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Item Name",
        },
        "display_name": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Display Name",
        },
        "requested_effect": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Requested Effect",
        },
    }
    assert exchange_item_tool.args == {
        "item_id": {"title": "Item Id", "type": "string"},
        "price": {"title": "Price", "type": "integer"},
    }


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
            "category": "consumable",
            "craft_item": craft_item_and_store_reward,
            "random": FixedRandom(d20=[6]),
            "game_state": GameStateRepository(store),
        }
    )

    assert isinstance(result, ToolResult)
    assert result.raw["success"] is False
    assert result.raw["item_name"] == "healing_potion"
    assert result.raw["display_name"] == "회복 포션"
    assert result.raw["inventory_delta"] is None
    assert result.metadata["system_event"] == "tool.craft.completed"


def test_exchange_item_tool_returns_internal_dataclass() -> None:
    store = LangGraphStoreAdapter(InMemoryStore())
    result = exchange_item_tool.invoke(
        {
            "item_id": "travel_ration",
            "price": 15,
            "exchange_item": exchange_item,
            "game_state": GameStateRepository(store),
        }
    )

    assert isinstance(result, ToolResult)
    assert result.raw["item_id"] == "travel_ration"
    assert result.raw["price"] == 15
    assert result.raw["player_gold"] == 85
    assert result.metadata["system_event"] == "tool.trade.exchange.completed"
