from typing import Protocol


class IScoreColorizer(Protocol):
    def colorize(self, score: int) -> str: ...
