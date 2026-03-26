from typing import Any, Protocol


class IPropertyValueTransformer(Protocol):
    def get_value(self, prop: Any, field_name: str) -> Any: ...
