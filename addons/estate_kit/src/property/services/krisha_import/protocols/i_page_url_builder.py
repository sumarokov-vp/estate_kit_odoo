from typing import Protocol


class IPageUrlBuilder(Protocol):
    def build(self, base_url: str, page: int) -> str: ...
