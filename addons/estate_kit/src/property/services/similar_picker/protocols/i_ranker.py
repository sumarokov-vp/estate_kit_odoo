from typing import Protocol


class IRanker(Protocol):
    def rank(self, prop, candidates, limit: int): ...
