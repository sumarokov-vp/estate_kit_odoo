from typing import Protocol


class IAddressFormatter(Protocol):
    def format(self, prop) -> str: ...
