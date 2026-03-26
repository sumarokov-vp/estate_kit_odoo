from typing import Protocol


class IPoolTagFinder(Protocol):
    def find(self, env): ...
