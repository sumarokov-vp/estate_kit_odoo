from typing import Protocol


class IEventCleaner(Protocol):
    def cleanup(self, retention_days: int) -> None: ...
