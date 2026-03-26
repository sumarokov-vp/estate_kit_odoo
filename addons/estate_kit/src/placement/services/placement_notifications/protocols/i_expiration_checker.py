from typing import Protocol


class IExpirationChecker(Protocol):
    def expire(self, env) -> None: ...
