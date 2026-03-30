from typing import Any, Protocol


class ICriteriaCollector(Protocol):
    def collect(self, lead: Any) -> dict: ...
