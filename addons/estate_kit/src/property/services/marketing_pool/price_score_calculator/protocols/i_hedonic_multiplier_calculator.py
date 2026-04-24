from dataclasses import dataclass
from typing import Protocol

from ..hedonic_factor import HedonicFactor


@dataclass(frozen=True)
class HedonicMultiplierResult:
    multiplier: float
    factors_applied: list[HedonicFactor]


class IHedonicMultiplierCalculator(Protocol):
    def calculate(self, prop) -> HedonicMultiplierResult: ...
