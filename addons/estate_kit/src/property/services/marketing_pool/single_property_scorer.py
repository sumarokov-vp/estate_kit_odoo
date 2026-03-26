from .protocols import IMpsCalculator


class SinglePropertyScorer:
    def __init__(self, calculator: IMpsCalculator):
        self._calculator = calculator

    def update(self, prop) -> None:
        latest = prop.scoring_ids[:1]
        if not latest:
            return

        result = self._calculator.calculate(prop, latest)
        prop.write({
            "marketing_pool_score": result.score,
            "marketing_pool_score_display": result.display,
        })
