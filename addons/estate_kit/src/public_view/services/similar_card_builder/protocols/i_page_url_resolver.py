from typing import Protocol


class IPageUrlResolver(Protocol):
    def resolve(self, prop) -> str: ...
