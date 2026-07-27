from typing import Protocol


class IContactBuilder(Protocol):
    def build(self, prop) -> dict: ...
