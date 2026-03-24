from typing import Any

from .match_result import MatchResult
from .protocols import IHttpClient
from .search_criteria import SearchCriteria


class MatchingClientService:
    def __init__(self, http_client: IHttpClient) -> None:
        self._http = http_client

    def search(self, criteria: SearchCriteria, limit: int = 50) -> list[MatchResult]:
        body = self._build_body(criteria, limit)
        data = self._http.post("/search", body)
        return [self._map_result(item) for item in data.get("results", [])]

    def _build_body(self, criteria: SearchCriteria, limit: int) -> dict[str, Any]:
        body: dict[str, Any] = {"limit": limit}
        if criteria.deal_type:
            body["deal_type"] = criteria.deal_type
        if criteria.property_type:
            body["property_type"] = criteria.property_type
        if criteria.city:
            body["city"] = criteria.city
        if criteria.districts:
            body["districts"] = criteria.districts
        if criteria.rooms_min is not None:
            body["rooms_min"] = criteria.rooms_min
        if criteria.rooms_max is not None:
            body["rooms_max"] = criteria.rooms_max
        if criteria.price_min is not None:
            body["price_min"] = criteria.price_min
        if criteria.price_max is not None:
            body["price_max"] = criteria.price_max
        if criteria.area_min is not None:
            body["area_min"] = criteria.area_min
        if criteria.area_max is not None:
            body["area_max"] = criteria.area_max
        return body

    def _map_result(self, item: dict[str, Any]) -> MatchResult:
        return MatchResult(
            property_id=item["id"],
            score=float(item.get("score", 0.0)),
        )
