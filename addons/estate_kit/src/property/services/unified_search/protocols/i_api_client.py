from typing import Any, Protocol


class IApiClient(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None: ...
