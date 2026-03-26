from typing import Protocol


class IThresholdChecker(Protocol):
    def scores_below_threshold(
        self, scoring, min_price: int, min_quality: int, min_listing: int,
    ) -> bool: ...
