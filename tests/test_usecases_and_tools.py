from __future__ import annotations

from langgraph.store.memory import InMemoryStore

from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.usecases import (
    craft_item,
    craft_item_and_store_reward,
    resolve_battle_action,
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


def test_tool_schema_hides_injected_dependencies() -> None:
    assert resolve_battle_tool.args == {"action": {"title": "Action", "type": "string"}}
    assert craft_item_tool.args == {"recipe": {"title": "Recipe", "type": "string"}}


def test_resolve_battle_tool_returns_internal_dataclass() -> None:
    result = resolve_battle_tool.invoke(
        {
            "action": "attack",
            "resolve_battle_action": resolve_battle_action,
            "random": FixedRandom(d20=[12], damage=[8]),
        }
    )

    assert isinstance(result, ToolResult)
    assert result.raw["outcome"] == BattleOutcome.HIT.value
    assert result.raw["damage"] == 8
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
