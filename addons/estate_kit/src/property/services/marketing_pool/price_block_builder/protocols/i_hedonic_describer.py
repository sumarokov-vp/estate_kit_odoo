from typing import Protocol

from ...price_score_calculator.hedonic_factor import HedonicFactor


class IHedonicDescriber(Protocol):
    def describe(
        self,
        factors: list[HedonicFactor],
        multiplier: float,
        median_per_sqm: float,
        expected_per_sqm: float,
    ) -> list[str]: ...
