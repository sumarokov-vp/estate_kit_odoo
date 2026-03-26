from typing import Protocol


class IBatchPropertyScorer(Protocol):
    def score_all(self, properties) -> tuple[dict, list[str]]: ...
