from typing import Any

from ..matching_client import SearchCriteria
from .protocols import IMatchingClient, IMatchingRequestLogger, IMatchRepository

_LOG_CATEGORY = "matching"


class LeadMatcherService:
    def __init__(
        self,
        matching_client: IMatchingClient,
        match_repository: IMatchRepository,
        request_logger: IMatchingRequestLogger,
        env: Any,
    ) -> None:
        self._matching_client = matching_client
        self._match_repository = match_repository
        self._request_logger = request_logger
        self._env = env

    def match(self, lead_id: int, criteria: SearchCriteria) -> int:
        """Run matching for a lead. Returns count of matches found."""
        Log = self._env["estate.kit.log"]

        self._request_logger.log(Log, lead_id, criteria)

        results = self._matching_client.search(criteria)
        count = self._match_repository.sync(lead_id, results)

        if results:
            top = results[:5]
            lines = ["ID=%d, score=%.2f" % (r.property_id, r.score) for r in top]
            if len(results) > 5:
                lines.append("... и ещё %d" % (len(results) - 5))
            details = "\n".join(lines)
        else:
            details = "Совпадений не найдено"

        Log.log(
            _LOG_CATEGORY,
            "Результат подбора для лида #%d: найдено %d, синхронизировано %d"
            % (lead_id, len(results), count),
            details=details,
        )

        return count
