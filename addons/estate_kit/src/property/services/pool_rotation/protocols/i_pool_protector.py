from typing import Protocol


class IPoolProtector(Protocol):
    def is_pool_protected(self, prop) -> bool: ...
