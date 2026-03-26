from typing import Any, Protocol

import requests


class IApiClient(Protocol):
    api_url: str

    @property
    def is_configured(self) -> bool: ...

    def post_public(self, endpoint: str, data: dict[str, Any]) -> requests.Response | None: ...

    def get_public(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response | None: ...

    def get_raw(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response | None: ...

    def post_raw(self, endpoint: str, data: dict[str, Any]) -> requests.Response | None: ...
