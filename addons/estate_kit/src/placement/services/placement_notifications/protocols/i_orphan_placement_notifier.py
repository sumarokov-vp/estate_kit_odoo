from typing import Protocol


class IOrphanPlacementNotifier(Protocol):
    def notify(self, env) -> None: ...
