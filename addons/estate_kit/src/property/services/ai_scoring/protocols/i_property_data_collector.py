from typing import Protocol


class IPropertyDataCollector(Protocol):
    def collect(self, prop, benchmark=None) -> dict: ...
