from .protocols import (
    IDeviationCalculator,
    IHedonicMultiplierCalculator,
    IScoreMapper,
)
from .result import PriceScoreResult


class PriceScoreCalculator:
    def __init__(
        self,
        hedonic_calculator: IHedonicMultiplierCalculator,
        deviation_calculator: IDeviationCalculator,
        score_mapper: IScoreMapper,
    ) -> None:
        self._hedonic_calculator = hedonic_calculator
        self._deviation_calculator = deviation_calculator
        self._score_mapper = score_mapper

    def calculate(self, prop, benchmark) -> PriceScoreResult | None:
        if not prop.price or not prop.area_total or prop.area_total <= 0:
            return None

        actual_per_sqm = prop.price / prop.area_total
        hedonic_result = self._hedonic_calculator.calculate(prop)
        expected_per_sqm = benchmark.median_price_per_sqm * hedonic_result.multiplier
        deviation = self._deviation_calculator.calculate(
            actual_per_sqm, expected_per_sqm,
        )
        score = self._score_mapper.map(deviation)

        return PriceScoreResult(
            score=score,
            deviation=deviation,
            expected_per_sqm=expected_per_sqm,
            actual_per_sqm=actual_per_sqm,
            benchmark_snapshot_id=benchmark.snapshot_id,
            hedonic_multiplier=hedonic_result.multiplier,
            hedonic_factors_applied=hedonic_result.factors_applied,
        )
