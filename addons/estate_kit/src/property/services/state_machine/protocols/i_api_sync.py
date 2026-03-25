from typing import Any, Protocol


class IApiSync(Protocol):
    def push_property(self, record: Any) -> None: ...
