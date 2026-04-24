from typing import Protocol

from ...price_score_calculator.config import DeviationBucket


class IBucketDescriber(Protocol):
    def describe(
        self,
        bucket: DeviationBucket,
        buckets: tuple[DeviationBucket, ...],
    ) -> str: ...
