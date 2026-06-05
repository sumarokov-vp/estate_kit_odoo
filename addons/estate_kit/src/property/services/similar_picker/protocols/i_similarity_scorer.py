from typing import Protocol


class ISimilarityScorer(Protocol):
    def score(self, prop, candidate) -> float: ...
