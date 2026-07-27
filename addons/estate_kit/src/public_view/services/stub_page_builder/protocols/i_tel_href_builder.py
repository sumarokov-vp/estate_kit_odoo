from typing import Protocol


class ITelHrefBuilder(Protocol):
    def build(self, phone: str | None) -> str | None: ...
