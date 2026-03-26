from typing import Protocol


class ISinglePropertyScorer(Protocol):
    def update(self, prop) -> None: ...
