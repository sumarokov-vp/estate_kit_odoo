from typing import Protocol


class IPoolSummaryLogger(Protocol):
    def log(self, stats: dict, details_lines: list[str]) -> None: ...
