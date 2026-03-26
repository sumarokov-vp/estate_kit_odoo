from typing import Protocol


class IMarketingPool(Protocol):
    @property
    def is_configured(self) -> bool: ...

    @property
    def model(self) -> str: ...

    def score_property(self, property_data: dict) -> dict | None: ...
