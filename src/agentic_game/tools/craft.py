from __future__ import annotations

from typing import Annotated, Any

from langchain_core.tools import InjectedToolArg, tool

from agentic_game.tools.result_projection import craft_result_to_tool_result
from agentic_game.tools.types import ToolResult


@tool
def craft_item_tool(
    category: str,
    craft_item: Annotated[Any, InjectedToolArg],
    random: Annotated[Any, InjectedToolArg],
    game_state: Annotated[Any, InjectedToolArg],
    item_name: str | None = None,
    display_name: str | None = None,
    requested_effect: str | None = None,
) -> ToolResult:
    """Craft an item from a general item category and optional item details."""
    result = craft_item(
        category,
        item_name=item_name,
        display_name=display_name,
        requested_effect=requested_effect,
        random=random,
        game_state=game_state,
    )
    return craft_result_to_tool_result(result)
