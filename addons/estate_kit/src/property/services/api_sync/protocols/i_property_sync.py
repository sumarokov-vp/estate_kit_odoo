from typing import Any, Protocol


class IPropertySync(Protocol):
    def push_property(self, record: Any) -> None: ...

    def push_owner(self, record: Any) -> Any: ...
