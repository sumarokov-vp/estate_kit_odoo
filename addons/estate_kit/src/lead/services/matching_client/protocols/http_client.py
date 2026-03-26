from typing import Any, Protocol


class IHttpClient(Protocol):
    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]: ...
