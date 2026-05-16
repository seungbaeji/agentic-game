from __future__ import annotations

from agentic_game.application.ports import RandomPort
from agentic_game.domain.craft import CraftResult, craft_result


def craft_item(
    recipe: str,
    *,
    random: RandomPort,
) -> CraftResult:
    """Run the craft item use case with injected randomness."""
    return craft_result(recipe=recipe, dice=random.roll_d20())
