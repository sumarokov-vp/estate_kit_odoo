from .protocols import IListingFetcher, ISleeper


class KrishaSnapshotFetcher:
    def __init__(
        self,
        listing_fetcher: IListingFetcher,
        sleeper: ISleeper,
        inter_page_sleep_seconds: float,
    ) -> None:
        self._listing_fetcher = listing_fetcher
        self._sleeper = sleeper
        self._inter_page_sleep_seconds = inter_page_sleep_seconds

    def fetch_price_per_sqm_samples(
        self, search_url: str, max_pages: int,
    ) -> list[float]:
        samples: list[float] = []
        for page in range(1, max_pages + 1):
            items = self._listing_fetcher.fetch(search_url, page)
            if not items:
                break
            for item in items:
                price = item.get("price")
                area = item.get("area")
                if not price or not area:
                    continue
                try:
                    price_float = float(price)
                    area_float = float(area)
                except (TypeError, ValueError):
                    continue
                if price_float <= 0 or area_float <= 0:
                    continue
                samples.append(price_float / area_float)
            if page < max_pages:
                self._sleeper.sleep(self._inter_page_sleep_seconds)
        return samples
