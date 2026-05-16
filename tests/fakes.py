from __future__ import annotations

from collections import deque


class FixedRandom:
    def __init__(self, *, d20: list[int], damage: list[int] | None = None) -> None:
        self._d20 = deque(d20)
        self._damage = deque(damage or [])

    def roll_d20(self) -> int:
        return self._d20.popleft()

    def roll_damage(self, low: int, high: int) -> int:
        if self._damage:
            return self._damage.popleft()
        return low
