import logging

from .protocols import (
    IConfigProvider,
    IDetailFetcher,
    IDuplicateChecker,
    IImportLogger,
    IListingFetcher,
    IPhotoImporter,
    IPropertyCreator,
)
from .result import KrishaImportResult

_logger = logging.getLogger(__name__)


class KrishaImportService:
    def __init__(
        self,
        config_provider: IConfigProvider,
        listing_fetcher: IListingFetcher,
        detail_fetcher: IDetailFetcher,
        duplicate_checker: IDuplicateChecker,
        property_creator: IPropertyCreator,
        photo_importer: IPhotoImporter,
        logger: IImportLogger,
    ) -> None:
        self._config_provider = config_provider
        self._listing_fetcher = listing_fetcher
        self._detail_fetcher = detail_fetcher
        self._duplicate_checker = duplicate_checker
        self._property_creator = property_creator
        self._photo_importer = photo_importer
        self._logger = logger

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
            "Krisha import started: url=%s limit=%s",
            config.search_url,
            config.limit,
        )
        items = self._listing_fetcher.fetch(config.search_url, config.limit)
        _logger.info("Krisha import: fetched %d listings", len(items))

        imported = 0
        duplicates = 0
        errors = 0
        for index, item in enumerate(items, start=1):
            url = item.get("url", "")
            _logger.info("Krisha import [%d/%d]: %s", index, len(items), url)
            try:
                if self._duplicate_checker.is_imported(url):
                    _logger.info("Krisha import [%d/%d]: duplicate %s", index, len(items), url)
                    self._logger.log_duplicate(url)
                    duplicates += 1
                    continue
                detail = self._detail_fetcher.fetch(url)
                detail["url"] = url
                property_id = self._property_creator.create(detail)
                self._photo_importer.import_photos(property_id, detail.get("photo_urls", []))
                _logger.info(
                    "Krisha import [%d/%d]: imported property_id=%s url=%s",
                    index,
                    len(items),
                    property_id,
                    url,
                )
                self._logger.log_success(url, property_id, detail)
                imported += 1
            except Exception as exc:
                _logger.exception(
                    "Krisha import [%d/%d]: error url=%s: %s",
                    index,
                    len(items),
                    url,
                    exc,
                )
                self._logger.log_error(url, exc)
                errors += 1

        _logger.info(
            "Krisha import finished: imported=%d duplicates=%d errors=%d",
            imported,
            duplicates,
            errors,
        )
        self._logger.log_summary(imported, duplicates, errors)
        return KrishaImportResult(imported=imported, duplicates=duplicates, errors=errors)
