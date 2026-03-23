from typing import Protocol


class IPoolStatusBuilder(Protocol):
    def build(self, prop, scoring) -> str: ...
