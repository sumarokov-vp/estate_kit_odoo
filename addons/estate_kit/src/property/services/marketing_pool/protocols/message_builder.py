from typing import Any, Protocol


class IMessageBuilder(Protocol):
    def build(self, property_data: dict[str, Any]) -> str: ...
