from typing import Any, Protocol


class IBuildingTypeResolver(Protocol):
    def resolve(self, raw: Any) -> str | None: ...
