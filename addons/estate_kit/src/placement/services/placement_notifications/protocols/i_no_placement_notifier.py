from typing import Protocol


class INoPlacementNotifier(Protocol):
    def notify(self, env) -> None: ...
