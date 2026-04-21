from typing import Protocol


class IRoomsExtractor(Protocol):
    def extract(self, title: str) -> int: ...
