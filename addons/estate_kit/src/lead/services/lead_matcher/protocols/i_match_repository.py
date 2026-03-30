from typing import Protocol

from ...matching_client import MatchResult


class IMatchRepository(Protocol):
    def sync(self, lead_id: int, results: list[MatchResult]) -> int:
        """Sync match records for a lead. Returns count of current matches."""
        ...
