from .config import SnapshotTarget
from .protocols import ITargetFormatter

_CATEGORY = "market_snapshot"


class SnapshotLogger:
    def __init__(self, env, target_formatter: ITargetFormatter) -> None:
        self._env = env
        self._target_formatter = target_formatter

    def log_start(self, targets_count: int) -> None:
        self._env["estate.kit.log"].log(
            _CATEGORY,
            "Сбор снапшотов рынка запущен: %d целей" % targets_count,
        )

    def log_target_skipped(self, target: SnapshotTarget, reason: str) -> None:
        self._env["estate.kit.log"].log(
            _CATEGORY,
            "Срез пропущен: %s" % self._target_formatter.format(target),
            details=reason,
            level="warning",
        )

    def log_target_success(
        self, target: SnapshotTarget, sample_size: int, median: float,
    ) -> None:
        self._env["estate.kit.log"].log(
            _CATEGORY,
            "Снапшот записан: %s" % self._target_formatter.format(target),
            details="выборка=%d, медиана за м²=%.0f KZT" % (sample_size, median),
        )

    def log_target_failure(self, target: SnapshotTarget, error: str) -> None:
        self._env["estate.kit.log"].log(
            _CATEGORY,
            "Ошибка сбора среза: %s" % self._target_formatter.format(target),
            details=error,
            level="error",
        )

    def log_summary(self, written: int, skipped: int, errors: int) -> None:
        self._env["estate.kit.log"].log(
            _CATEGORY,
            "Сбор снапшотов завершён: записано=%d, пропущено=%d, ошибок=%d"
            % (written, skipped, errors),
        )
