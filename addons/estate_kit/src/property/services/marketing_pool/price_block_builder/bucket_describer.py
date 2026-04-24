from ..price_score_calculator.config import DeviationBucket
from .protocols import INumberFormatter


class BucketDescriber:
    def __init__(self, number_formatter: INumberFormatter) -> None:
        self._number_formatter = number_formatter

    def describe(
        self,
        bucket: DeviationBucket,
        buckets: tuple[DeviationBucket, ...],
    ) -> str:
        upper_percent = bucket.upper_bound * 100
        index = buckets.index(bucket)
        if index == 0:
            return "«≤%s»" % self._number_formatter.format_percent_signed(upper_percent)
        previous = buckets[index - 1]
        if bucket.upper_bound == float("inf"):
            return "«>%s»" % self._number_formatter.format_percent_signed(previous.upper_bound * 100)
        lower = self._number_formatter.format_percent_signed(previous.upper_bound * 100)
        upper = self._number_formatter.format_percent_signed(upper_percent)
        return "«%s…%s»" % (lower, upper)
