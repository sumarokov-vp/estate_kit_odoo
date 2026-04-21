from typing import Protocol


class IPriceParser(Protocol):
    def parse(self, text: str) -> int: ...
