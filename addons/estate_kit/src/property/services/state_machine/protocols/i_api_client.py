from typing import Any, Protocol


class IApiClient(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any] | None: ...
