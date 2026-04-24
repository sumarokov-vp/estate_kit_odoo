from typing import Protocol


class IPropertyTypeNormalizer(Protocol):
    def normalize(self, property_type: str) -> str: ...
