from typing import Protocol


class IFreshnessChecker(Protocol):
    def ensure_fresh(self, properties) -> None: ...
