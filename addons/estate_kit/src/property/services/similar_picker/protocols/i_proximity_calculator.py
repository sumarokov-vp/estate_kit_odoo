from typing import Protocol


class IProximityCalculator(Protocol):
    def calculate(
        self, base: float, value: float, tolerance: float, weight: float
    ) -> float: ...
