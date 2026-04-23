from typing import Protocol

from ..config import SnapshotTarget


class ITargetFormatter(Protocol):
    def format(self, target: SnapshotTarget) -> str: ...
