from typing import Protocol

from ..config import SnapshotTarget
from .i_price_stats_calculator import PriceStats


class ISnapshotWriter(Protocol):
    def write(self, target: SnapshotTarget, stats: PriceStats) -> int: ...
