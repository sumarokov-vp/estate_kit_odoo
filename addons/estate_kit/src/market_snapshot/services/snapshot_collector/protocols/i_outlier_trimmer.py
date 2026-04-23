from typing import Protocol


class IOutlierTrimmer(Protocol):
    def trim(self, samples: list[float]) -> list[float]: ...
