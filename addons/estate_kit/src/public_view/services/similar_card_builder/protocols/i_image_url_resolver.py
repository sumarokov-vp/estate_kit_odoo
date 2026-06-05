from typing import Protocol


class IImageUrlResolver(Protocol):
    def resolve(self, prop) -> str | None: ...
