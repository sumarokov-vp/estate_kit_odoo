from typing import Any, Protocol

from ...matching_client import SearchCriteria


class IMatchingRequestLogger(Protocol):
    def log(self, Log: Any, lead_id: int, criteria: SearchCriteria) -> None: ...
