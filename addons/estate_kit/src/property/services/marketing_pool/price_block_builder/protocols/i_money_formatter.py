from typing import Protocol


class IMoneyFormatter(Protocol):
    def format(self, value: float) -> str: ...
