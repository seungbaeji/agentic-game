from __future__ import annotations

import random


class RandomAdapter:
    def roll_d20(self) -> int:
        """Roll a random twenty-sided die."""
        return random.randint(1, 20)

    def roll_damage(self, low: int, high: int) -> int:
        """Roll random damage within the inclusive low/high range."""
        return random.randint(low, high)
