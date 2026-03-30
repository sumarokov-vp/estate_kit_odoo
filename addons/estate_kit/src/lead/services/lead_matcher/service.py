from ..matching_client import SearchCriteria
from .protocols import IMatchingClient, IMatchRepository


class LeadMatcherService:
    def __init__(
        self,
        matching_client: IMatchingClient,
        match_repository: IMatchRepository,
    ) -> None:
        self._matching_client = matching_client
        self._match_repository = match_repository

    def match(self, lead_id: int, criteria: SearchCriteria) -> int:
        """Run matching for a lead. Returns count of matches found."""
        results = self._matching_client.search(criteria)
        return self._match_repository.sync(lead_id, results)
