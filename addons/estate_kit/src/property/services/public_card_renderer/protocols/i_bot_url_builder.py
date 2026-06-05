from typing import Protocol


class IBotUrlBuilder(Protocol):
    def build(self, token: str) -> str | None: ...
