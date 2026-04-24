from typing import Protocol


class IPropertyTypeLabelResolver(Protocol):
    def resolve(self, property_type: str) -> str: ...
