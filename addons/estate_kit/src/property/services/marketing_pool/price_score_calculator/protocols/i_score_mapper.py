from typing import Protocol

from ..config import DeviationBucket


class IScoreMapper(Protocol):
    def map(self, deviation: float) -> DeviationBucket: ...
