from typing import Protocol


class IMarketingPool(Protocol):
    def calculate_all(self) -> None: ...

    def scores_below_threshold(self, scoring, min_price: int, min_quality: int, min_listing: int) -> bool: ...
