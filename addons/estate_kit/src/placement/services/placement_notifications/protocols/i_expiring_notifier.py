from typing import Protocol


class IExpiringNotifier(Protocol):
    def notify(self, env) -> None: ...
