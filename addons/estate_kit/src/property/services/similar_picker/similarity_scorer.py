from .config import RESIDENTIAL_TYPES, ScoringConfig
from .protocols import IProximityCalculator


class SimilarityScorer:
    def __init__(
        self, config: ScoringConfig, proximity_calculator: IProximityCalculator
    ) -> None:
        self._config = config
        self._proximity_calculator = proximity_calculator

    def score(self, prop, candidate) -> float:
        cfg = self._config
        total = 0.0

        if prop.district_id and candidate.district_id == prop.district_id:
            total += cfg.same_district_weight

        total += self._proximity_calculator.calculate(
            prop.price, candidate.price, cfg.price_tolerance, cfg.price_weight
        )
        total += self._proximity_calculator.calculate(
            prop.area_total, candidate.area_total, cfg.area_tolerance, cfg.area_weight
        )

        if prop.property_type in RESIDENTIAL_TYPES and prop.rooms:
            diff = abs((candidate.rooms or 0) - prop.rooms)
            if diff <= cfg.rooms_tolerance:
                total += cfg.rooms_weight * (1 - diff / (cfg.rooms_tolerance + 1))
            else:
                total -= cfg.rooms_weight

        return total
