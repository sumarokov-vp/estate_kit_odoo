from typing import Protocol

from ...marketing_pool.price_score_calculator.result import PriceScoreResult


class IPriceScoreCalculator(Protocol):
    def calculate(self, prop, benchmark) -> PriceScoreResult | None: ...
