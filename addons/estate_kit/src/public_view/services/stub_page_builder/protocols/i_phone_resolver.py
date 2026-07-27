from typing import Protocol


class IPhoneResolver(Protocol):
    def resolve(self, prop) -> str | None: ...
