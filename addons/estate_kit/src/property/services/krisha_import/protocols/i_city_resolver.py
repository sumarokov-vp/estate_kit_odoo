from typing import Any, Protocol


class ICityResolver(Protocol):
    def resolve(self, city_name: Any) -> int | None: ...
