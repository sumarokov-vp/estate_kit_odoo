from typing import Protocol


class ITierMaxLimitValidator(Protocol):
    def validate_max_limit(self, records) -> None: ...
