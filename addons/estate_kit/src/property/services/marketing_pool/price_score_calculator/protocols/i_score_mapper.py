from typing import Protocol


class IScoreMapper(Protocol):
    def map(self, deviation: float) -> int: ...
