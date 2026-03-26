from typing import Protocol


class IApiActionCaller(Protocol):
    def call_action(self, records, action: str) -> None: ...
