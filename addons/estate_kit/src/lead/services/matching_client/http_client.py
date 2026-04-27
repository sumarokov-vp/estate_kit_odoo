from typing import Any

import requests

from .exceptions import MatchingServiceUnavailableError
from .protocols import IHttpClient


class HttpClient:
    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = self._base_url + path
        try:
            response = requests.post(url, json=body, timeout=self._timeout)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            raise MatchingServiceUnavailableError(str(exc)) from exc
        response.raise_for_status()
        return response.json()


_: IHttpClient = HttpClient.__new__(HttpClient)
