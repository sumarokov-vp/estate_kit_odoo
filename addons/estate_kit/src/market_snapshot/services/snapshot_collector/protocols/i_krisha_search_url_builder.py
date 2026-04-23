from typing import Protocol

from ..config import SnapshotTarget


class IKrishaSearchUrlBuilder(Protocol):
    def build(self, target: SnapshotTarget) -> str | None: ...
