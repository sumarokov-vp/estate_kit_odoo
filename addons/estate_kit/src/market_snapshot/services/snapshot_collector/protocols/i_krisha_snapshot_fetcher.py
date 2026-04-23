from typing import Protocol


class IKrishaSnapshotFetcher(Protocol):
    def fetch_price_per_sqm_samples(
        self, search_url: str, max_pages: int,
    ) -> list[float]: ...
