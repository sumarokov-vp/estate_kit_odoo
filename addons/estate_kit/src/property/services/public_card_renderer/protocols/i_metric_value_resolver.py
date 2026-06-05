from typing import Protocol


class IMetricValueResolver(Protocol):
    def resolve(self, prop, spec) -> str | None: ...
