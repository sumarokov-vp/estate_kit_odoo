from typing import Protocol


class IFeaturesCollector(Protocol):
    def collect(self, prop) -> list[str]: ...
