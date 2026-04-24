from typing import Protocol

from ...price_score_calculator.config import DeviationBucket


class IPriceScoreConfigProvider(Protocol):
    def get_buckets(self) -> tuple[DeviationBucket, ...]: ...
