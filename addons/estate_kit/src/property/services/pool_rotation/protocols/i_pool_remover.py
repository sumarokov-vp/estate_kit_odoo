from typing import Protocol


class IPoolRemover(Protocol):
    def remove(self, prop, pool_tag, reason: str) -> None: ...
