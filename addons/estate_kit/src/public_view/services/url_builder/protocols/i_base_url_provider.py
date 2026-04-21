from typing import Protocol


class IBaseUrlProvider(Protocol):
    def get(self) -> str: ...
