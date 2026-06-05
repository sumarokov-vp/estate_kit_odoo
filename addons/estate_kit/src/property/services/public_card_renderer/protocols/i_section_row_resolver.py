from typing import Protocol


class ISectionRowResolver(Protocol):
    def resolve(self, prop, spec) -> tuple[str, str] | None: ...
