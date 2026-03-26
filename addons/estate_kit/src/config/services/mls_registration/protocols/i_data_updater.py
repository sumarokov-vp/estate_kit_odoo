from typing import Any, Protocol


class IDataUpdater(Protocol):
    def update(self, settings: Any) -> dict: ...
