from typing import Protocol


class IStateBadgeBuilder(Protocol):
    def build(self, prop) -> dict | None: ...
