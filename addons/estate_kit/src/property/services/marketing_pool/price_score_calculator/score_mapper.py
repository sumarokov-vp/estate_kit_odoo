from .config import DeviationBucket


class ScoreMapper:
    def __init__(self, buckets: tuple[DeviationBucket, ...]) -> None:
        self._buckets = buckets

    def map(self, deviation: float) -> DeviationBucket:
        for bucket in self._buckets:
            if deviation <= bucket.upper_bound:
                return bucket
        return self._buckets[-1]
