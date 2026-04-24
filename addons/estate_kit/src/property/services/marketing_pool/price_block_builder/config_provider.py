from ..price_score_calculator.config import DeviationBucket
from ..price_score_calculator.config_provider import PriceScoreConfigProvider


class PriceScoreConfigProviderAdapter:
    def __init__(self, provider: PriceScoreConfigProvider) -> None:
        self._provider = provider

    def get_buckets(self) -> tuple[DeviationBucket, ...]:
        return self._provider.load().deviation_buckets
