from typing import Protocol


class ISpecsFormatter(Protocol):
    def format(self, prop) -> str: ...
