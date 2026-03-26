from typing import Protocol


class IMlsPropertySearcher(Protocol):
    def search_mls(self, criteria: dict, limit: int, offset: int) -> list: ...
