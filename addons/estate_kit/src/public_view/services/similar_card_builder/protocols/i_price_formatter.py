from typing import Protocol


class IPriceFormatter(Protocol):
    def format(self, prop) -> str: ...
