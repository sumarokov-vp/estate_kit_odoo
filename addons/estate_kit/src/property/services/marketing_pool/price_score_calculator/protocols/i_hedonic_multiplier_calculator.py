from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class HedonicMultiplierResult:
    multiplier: float
    factors_applied: list[str]


class IHedonicMultiplierCalculator(Protocol):
    def calculate(self, prop) -> HedonicMultiplierResult: ...
