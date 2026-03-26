from .protocols import ILocalPropertySearcher, IMlsPropertySearcher


class UnifiedSearchService:
    def __init__(
        self,
        local_searcher: ILocalPropertySearcher,
        mls_searcher: IMlsPropertySearcher,
    ) -> None:
        self._local_searcher = local_searcher
        self._mls_searcher = mls_searcher

    def search_unified(self, criteria: dict, limit: int = 50, offset: int = 0, count: bool = False) -> list | int:
        criteria = criteria or {}
        local_results = self._local_searcher.search_local(criteria, limit, offset)
        mls_results = self._mls_searcher.search_mls(criteria, limit, offset)

        local_mls_ids = {r["mls_id"] for r in local_results if r.get("mls_id")}
        merged = list(local_results)
        for item in mls_results:
            if item.get("mls_id") and item["mls_id"] not in local_mls_ids:
                merged.append(item)

        if count:
            return len(merged)

        return merged[:limit]
