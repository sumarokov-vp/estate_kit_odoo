class ThresholdChecker:
    def scores_below_threshold(
        self, scoring, min_price: int, min_quality: int, min_listing: int,
    ) -> bool:
        return (
            scoring.price_score < min_price
            or scoring.quality_score < min_quality
            or scoring.listing_score < min_listing
        )
