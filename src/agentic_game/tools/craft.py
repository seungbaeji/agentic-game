from __future__ import annotations

from typing import Annotated, Any

from langchain_core.tools import InjectedToolArg, tool

from agentic_game.tools.projections import craft_result_to_tool_result
from agentic_game.tools.types import ToolResult


@tool
def craft_item_tool(
    recipe: str,
    craft_item: Annotated[Any, InjectedToolArg],
    random: Annotated[Any, InjectedToolArg],
    game_state: Annotated[Any, InjectedToolArg],
) -> ToolResult:
    """Craft an item. Input recipe must be potion or sword."""
    result = craft_item(recipe, random=random, game_state=game_state)
    return craft_result_to_tool_result(result)
