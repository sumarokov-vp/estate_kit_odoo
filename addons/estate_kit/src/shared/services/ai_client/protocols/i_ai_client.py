from typing import Protocol


class IAiClient(Protocol):
    @property
    def is_configured(self) -> bool: ...

    @property
    def model(self) -> str: ...

    def complete(self, system: str, user: str) -> str | None: ...
