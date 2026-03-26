from typing import Any, Protocol


class IActivityCreator(Protocol):
    def create(self, prop: Any, summary: str, note: str) -> None: ...
