import requests

from .config import DEFAULT_HEADERS, DEFAULT_TIMEOUT


class HttpSession:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)
        self._timeout = timeout

    def get_text(self, url: str) -> str:
        response = self._session.get(url, timeout=self._timeout)
        response.raise_for_status()
        return response.text

    def get_bytes(self, url: str) -> bytes:
        response = self._session.get(url, timeout=self._timeout)
        response.raise_for_status()
        return response.content
