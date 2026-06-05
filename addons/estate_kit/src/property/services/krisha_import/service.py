import itertools
import logging

from .protocols import (
    IConfigProvider,
    IImportLogger,
    IListingFetcher,
    ISingleItemImporter,
)
from .result import KrishaImportResult, SingleImportResult

_logger = logging.getLogger(__name__)

_MAX_PAGES = 50


class KrishaImportService:
    def __init__(
        self,
        config_provider: IConfigProvider,
        listing_fetcher: IListingFetcher,
        single_item_importer: ISingleItemImporter,
        logger: IImportLogger,
    ) -> None:
        self._config_provider = config_provider
        self._listing_fetcher = listing_fetcher
        self._single_item_importer = single_item_importer
        self._logger = logger

    def import_one(self, url: str) -> SingleImportResult:
        _logger.info("Krisha single import: %s", url)
        return self._single_item_importer.import_one(url)

    def import_batch(self) -> KrishaImportResult:
        config = self._config_provider.load()
        if not config.search_url:
            skipped_reason = "URL не настроен"
            _logger.info("Krisha import skipped: %s", skipped_reason)
            self._logger.log_summary(
                imported=0,
                duplicates=0,
                errors=0,
                skipped_reason=skipped_reason,
            )
            return KrishaImportResult(
                imported=0,
                duplicates=0,
                errors=0,
                skipped_reason=skipped_reason,
            )

        _logger.info(
            "Krisha import started: url=%s import_target=%s",
            config.search_url,
            config.limit,
        )

        imported = 0
        duplicates = 0
        errors = 0
        overall_index = 0
        limit_reached = False

        for page in itertools.count(1):
            if page > _MAX_PAGES:
                _logger.warning(
                    "Krisha import: max pages reached, page=%d max=%d",
                    page,
                    _MAX_PAGES,
                )
                break

            _logger.info("Krisha import: fetching page=%d", page)
            items = self._listing_fetcher.fetch(config.search_url, page)
            _logger.info(
                "Krisha import: page=%d fetched %d listings",
                page,
                len(items),
            )

            if not items:
                break

            for item in items:
                if config.limit > 0 and imported >= config.limit:
                    _logger.info(
                        "Krisha import: limit reached, imported=%d limit=%d",
                        imported,
                        config.limit,
                    )
                    limit_reached = True
                    break
                overall_index += 1
                url = item.get("url", "")
                _logger.info("Krisha import [%d]: %s", overall_index, url)
                result = self._single_item_importer.import_one(url)
                if result.is_imported:
                    imported += 1
                elif result.is_duplicate:
                    duplicates += 1
                else:
                    errors += 1

            if limit_reached:
                break

        _logger.info(
            "Krisha import finished: imported=%d duplicates=%d errors=%d",
            imported,
            duplicates,
            errors,
        )
        self._logger.log_summary(imported, duplicates, errors)
        return KrishaImportResult(imported=imported, duplicates=duplicates, errors=errors)
