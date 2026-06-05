from typing import Protocol


class ITypeLabelResolver(Protocol):
    def resolve(self, prop) -> str: ...
