from typing import Protocol

from ...matching_client import MatchResult, SearchCriteria


class IMatchingClient(Protocol):
    def search(self, criteria: SearchCriteria, limit: int = 50) -> list[MatchResult]: ...
