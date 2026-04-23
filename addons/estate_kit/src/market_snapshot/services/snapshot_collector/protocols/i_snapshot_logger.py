from typing import Protocol

from ..config import SnapshotTarget


class ISnapshotLogger(Protocol):
    def log_start(self, targets_count: int) -> None: ...

    def log_target_skipped(self, target: SnapshotTarget, reason: str) -> None: ...

    def log_target_success(
        self, target: SnapshotTarget, sample_size: int, median: float,
    ) -> None: ...

    def log_target_failure(self, target: SnapshotTarget, error: str) -> None: ...

    def log_summary(self, written: int, skipped: int, errors: int) -> None: ...
