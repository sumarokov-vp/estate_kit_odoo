from typing import Protocol


class IHttpSession(Protocol):
    def get_bytes(self, url: str) -> bytes: ...

    def get_text(self, url: str) -> str: ...
