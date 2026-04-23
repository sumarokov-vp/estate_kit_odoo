from .protocols import (
    IKrishaSearchUrlBuilder,
    IKrishaSnapshotFetcher,
    IPriceStatsCalculator,
    ISleeper,
    ISnapshotConfigLoader,
    ISnapshotLogger,
    ISnapshotWriter,
)


class SnapshotCollectorService:
    def __init__(
        self,
        config_loader: ISnapshotConfigLoader,
        url_builder: IKrishaSearchUrlBuilder,
        fetcher: IKrishaSnapshotFetcher,
        stats_calculator: IPriceStatsCalculator,
        writer: ISnapshotWriter,
        logger: ISnapshotLogger,
        sleeper: ISleeper,
        inter_target_sleep_seconds: float,
    ) -> None:
        self._config_loader = config_loader
        self._url_builder = url_builder
        self._fetcher = fetcher
        self._stats_calculator = stats_calculator
        self._writer = writer
        self._logger = logger
        self._sleeper = sleeper
        self._inter_target_sleep_seconds = inter_target_sleep_seconds

    def collect_all(self) -> None:
        targets = self._config_loader.load()
        self._logger.log_start(len(targets))
        if not targets:
            self._logger.log_summary(written=0, skipped=0, errors=0)
            return

        written = 0
        skipped = 0
        errors = 0

        for index, target in enumerate(targets):
            is_last = index == len(targets) - 1
            search_url = self._url_builder.build(target)
            if not search_url:
                self._logger.log_target_skipped(
                    target, "Не удалось построить URL для Krisha",
                )
                skipped += 1
                continue

            try:
                samples = self._fetcher.fetch_price_per_sqm_samples(
                    search_url, target.max_pages,
                )
            except Exception as exc:
                self._logger.log_target_failure(target, str(exc))
                errors += 1
                if not is_last:
                    self._sleeper.sleep(self._inter_target_sleep_seconds)
                continue

            stats = self._stats_calculator.calculate(samples)
            if stats is None:
                self._logger.log_target_skipped(
                    target,
                    "Недостаточно данных: получено %d объявлений" % len(samples),
                )
                skipped += 1
                if not is_last:
                    self._sleeper.sleep(self._inter_target_sleep_seconds)
                continue

            try:
                self._writer.write(target, stats)
            except Exception as exc:
                self._logger.log_target_failure(target, str(exc))
                errors += 1
                if not is_last:
                    self._sleeper.sleep(self._inter_target_sleep_seconds)
                continue

            self._logger.log_target_success(
                target, stats.sample_size, stats.median_per_sqm,
            )
            written += 1
            if not is_last:
                self._sleeper.sleep(self._inter_target_sleep_seconds)

        self._logger.log_summary(written=written, skipped=skipped, errors=errors)
