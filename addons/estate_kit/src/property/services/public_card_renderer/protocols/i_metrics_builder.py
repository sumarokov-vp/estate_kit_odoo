from typing import Protocol


class IMetricsBuilder(Protocol):
    def build(self, prop) -> list[dict]: ...
