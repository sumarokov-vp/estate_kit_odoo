import itertools
import logging

from .protocols import (
    IConfigProvider,
    IDetailFetcher,
    IDuplicateChecker,
    IImportLogger,
    IListingFetcher,
    IPhotoImporter,
    IPropertyCreator,
    ITransactionScope,
)
from .result import KrishaImportResult

_logger = logging.getLogger(__name__)

_MAX_PAGES = 50


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
        transaction_scope: ITransactionScope,
    ) -> None:
        self._config_provider = config_provider
        self._listing_fetcher = listing_fetcher
        self._detail_fetcher = detail_fetcher
        self._duplicate_checker = duplicate_checker
        self._property_creator = property_creator
        self._photo_importer = photo_importer
        self._logger = logger
        self._transaction_scope = transaction_scope

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
                try:
                    if self._duplicate_checker.is_imported(url):
                        _logger.info("Krisha import [%d]: duplicate %s", overall_index, url)
                        self._logger.log_duplicate(url)
                        duplicates += 1
                        continue
                    with self._transaction_scope.savepoint():
                        detail = self._detail_fetcher.fetch(url)
                        detail["url"] = url
                        property_id = self._property_creator.create(detail)
                        self._photo_importer.import_photos(property_id, detail.get("photo_urls", []))
                    self._transaction_scope.commit()
                    _logger.info(
                        "Krisha import [%d]: imported property_id=%s url=%s",
                        overall_index,
                        property_id,
                        url,
                    )
                    self._logger.log_success(url, property_id, detail)
                    imported += 1
                except Exception as exc:
                    _logger.exception(
                        "Krisha import [%d]: error url=%s: %s",
                        overall_index,
                        url,
                        exc,
                    )
                    self._logger.log_error(url, exc)
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
