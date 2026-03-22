from typing import Protocol


class ITierBonusCalculator(Protocol):
    def calculate(self, prop) -> float: ...
