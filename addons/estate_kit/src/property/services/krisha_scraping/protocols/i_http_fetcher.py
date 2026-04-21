from typing import Protocol


class IHttpFetcher(Protocol):
    def fetch(self, url: str) -> str: ...
