from typing import Protocol

from ..config import SnapshotTarget


class ISnapshotConfigLoader(Protocol):
    def load(self) -> list[SnapshotTarget]: ...
