from typing import Protocol


class IDeviationCalculator(Protocol):
    def calculate(self, actual: float, expected: float) -> float: ...
