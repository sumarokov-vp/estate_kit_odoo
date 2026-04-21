from .protocols import (
    IConfigProvider,
    IDetailFetcher,
    IDuplicateChecker,
    IImportLogger,
    IListingFetcher,
    IPhotoImporter,
    IPropertyCreator,
)


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

    def import_batch(self) -> None:
        config = self._config_provider.load()
        if not config.search_url:
            self._logger.log_summary(
                imported=0,
                duplicates=0,
                errors=0,
                skipped_reason="URL не настроен",
            )
            return

        items = self._listing_fetcher.fetch(config.search_url, config.limit)

        imported = 0
        duplicates = 0
        errors = 0
        for item in items:
            url = item.get("url", "")
            try:
                if self._duplicate_checker.is_imported(url):
                    self._logger.log_duplicate(url)
                    duplicates += 1
                    continue
                detail = self._detail_fetcher.fetch(url)
                detail["url"] = url
                property_id = self._property_creator.create(detail)
                self._photo_importer.import_photos(property_id, detail.get("photo_urls", []))
                self._logger.log_success(url, property_id, detail)
                imported += 1
            except Exception as exc:
                self._logger.log_error(url, exc)
                errors += 1

        self._logger.log_summary(imported, duplicates, errors)
