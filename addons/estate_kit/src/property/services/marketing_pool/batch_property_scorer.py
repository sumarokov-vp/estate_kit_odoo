from .config import PoolScoreConfig
from .protocols import IMpsCalculator


class BatchPropertyScorer:
    def __init__(self, config: PoolScoreConfig, calculator: IMpsCalculator):
        self._config = config
        self._calculator = calculator

    def score_all(self, properties) -> tuple[dict, list[str]]:
        stats = {
            "total": len(properties),
            "no_scoring": 0,
            "below_price": 0,
            "below_quality": 0,
            "below_listing": 0,
            "below_inclusion": 0,
            "eligible": 0,
        }
        details_lines = []

        for prop in properties:
            latest = prop.scoring_ids[:1]
            if not latest:
                prop.write({
                    "marketing_pool_score": 0.0,
                    "marketing_pool_score_display": "— нет скоринга",
                })
                stats["no_scoring"] += 1
                continue

            result = self._calculator.calculate(prop, latest)
            prop.write({
                "marketing_pool_score": result.score,
                "marketing_pool_score_display": result.display,
            })

            failed_scores = []
            if latest.price_score < self._config.min_price:
                failed_scores.append("price=%d<%d" % (latest.price_score, self._config.min_price))
            if latest.quality_score < self._config.min_quality:
                failed_scores.append("quality=%d<%d" % (latest.quality_score, self._config.min_quality))
            if latest.listing_score < self._config.min_listing:
                failed_scores.append("listing=%d<%d" % (latest.listing_score, self._config.min_listing))

            if failed_scores:
                if latest.price_score < self._config.min_price:
                    stats["below_price"] += 1
                if latest.quality_score < self._config.min_quality:
                    stats["below_quality"] += 1
                if latest.listing_score < self._config.min_listing:
                    stats["below_listing"] += 1
                details_lines.append(
                    "%s: %s (отклонён по порогу)" % (prop.name, ", ".join(failed_scores))
                )
            elif result.score < self._config.t_include:
                stats["below_inclusion"] += 1
                details_lines.append(
                    "%s: MPS=%.1f < порог=%.1f (не включён)" % (prop.name, result.score, self._config.t_include)
                )
            else:
                stats["eligible"] += 1
                details_lines.append(
                    "%s: MPS=%.1f ✓ (кандидат в пул)" % (prop.name, result.score)
                )

        return stats, details_lines
