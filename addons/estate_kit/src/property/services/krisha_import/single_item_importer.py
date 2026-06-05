import logging

from .protocols import (
    IDetailFetcher,
    IDuplicateChecker,
    IImportLogger,
    IPhotoImporter,
    IPropertyCreator,
    ITransactionScope,
)
from .result import SingleImportResult, SingleImportStatus

_logger = logging.getLogger(__name__)


class SingleItemImporter:
    def __init__(
        self,
        detail_fetcher: IDetailFetcher,
        duplicate_checker: IDuplicateChecker,
        property_creator: IPropertyCreator,
        photo_importer: IPhotoImporter,
        logger: IImportLogger,
        transaction_scope: ITransactionScope,
    ) -> None:
        self._detail_fetcher = detail_fetcher
        self._duplicate_checker = duplicate_checker
        self._property_creator = property_creator
        self._photo_importer = photo_importer
        self._logger = logger
        self._transaction_scope = transaction_scope

    def import_one(self, url: str) -> SingleImportResult:
        try:
            if self._duplicate_checker.is_imported(url):
                _logger.info("Krisha import: duplicate %s", url)
                self._logger.log_duplicate(url)
                return SingleImportResult(status=SingleImportStatus.DUPLICATE, url=url)
            with self._transaction_scope.savepoint():
                detail = self._detail_fetcher.fetch(url)
                detail["url"] = url
                property_id = self._property_creator.create(detail)
                self._photo_importer.import_photos(property_id, detail.get("photo_urls", []))
            self._transaction_scope.commit()
            _logger.info("Krisha import: imported property_id=%s url=%s", property_id, url)
            self._logger.log_success(url, property_id, detail)
            return SingleImportResult(
                status=SingleImportStatus.IMPORTED,
                url=url,
                property_id=property_id,
            )
        except Exception as exc:
            _logger.exception("Krisha import: error url=%s: %s", url, exc)
            self._logger.log_error(url, exc)
            return SingleImportResult(
                status=SingleImportStatus.ERROR,
                url=url,
                error_message=str(exc),
            )
