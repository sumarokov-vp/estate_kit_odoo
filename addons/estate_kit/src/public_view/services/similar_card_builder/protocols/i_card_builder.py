from typing import Protocol


class ICardBuilder(Protocol):
    def build(self, prop) -> dict: ...
