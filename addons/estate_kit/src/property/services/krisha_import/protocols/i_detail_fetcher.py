from typing import Any, Protocol


class IDetailFetcher(Protocol):
    def fetch(self, krisha_url: str) -> dict[str, Any]: ...
