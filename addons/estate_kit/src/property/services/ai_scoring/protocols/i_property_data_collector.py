from typing import Protocol


class IPropertyDataCollector(Protocol):
    def collect(self, prop) -> dict: ...
