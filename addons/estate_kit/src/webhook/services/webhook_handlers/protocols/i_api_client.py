from typing import Any, Protocol


class IApiClient(Protocol):
    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None: ...
