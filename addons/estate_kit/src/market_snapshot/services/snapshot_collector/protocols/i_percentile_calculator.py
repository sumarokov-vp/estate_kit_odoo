from typing import Protocol


class IPercentileCalculator(Protocol):
    def calculate(self, sorted_samples: list[float], percentile: int) -> float: ...
