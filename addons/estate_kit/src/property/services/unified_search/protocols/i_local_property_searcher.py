from typing import Protocol


class ILocalPropertySearcher(Protocol):
    def search_local(self, criteria: dict, limit: int, offset: int) -> list: ...
