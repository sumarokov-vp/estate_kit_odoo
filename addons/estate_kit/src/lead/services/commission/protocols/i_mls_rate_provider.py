from typing import Any, Protocol


class IMlsRateProvider(Protocol):
    def get_rate(self, lead: Any) -> float | None: ...
