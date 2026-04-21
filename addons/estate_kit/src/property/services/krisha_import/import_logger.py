import traceback
from typing import Any

_LOG_CATEGORY = "external_parser"


class ImportLogger:
    def __init__(self, env) -> None:
        self._env = env

    def log_success(self, url: str, property_id: int, detail: dict[str, Any]) -> None:
        rooms = detail.get("rooms") or 0
        area = detail.get("area") or 0.0
        price = detail.get("price") or 0
        price_formatted = f"{int(price):,}".replace(",", " ")
        summary = (
            f"Импортирован объект #{property_id}: "
            f"{rooms}-комн, {area} м², {price_formatted} ₸"
        )
        self._env["estate.kit.log"].log(
            _LOG_CATEGORY,
            summary,
            details=url,
            level="info",
            property_id=property_id,
        )

    def log_duplicate(self, url: str) -> None:
        self._env["estate.kit.log"].log(
            _LOG_CATEGORY,
            f"Пропущен дубликат: {url}",
            level="info",
        )

    def log_error(self, url: str, exc: BaseException) -> None:
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self._env["estate.kit.log"].log(
            _LOG_CATEGORY,
            f"Ошибка импорта: {url}",
            details=details,
            level="error",
        )

    def log_summary(
        self,
        imported: int,
        duplicates: int,
        errors: int,
        skipped_reason: str | None = None,
    ) -> None:
        summary = (
            f"Импорт Krisha завершён: {imported} импортировано, "
            f"{duplicates} дубликатов, {errors} ошибок"
        )
        self._env["estate.kit.log"].log(
            _LOG_CATEGORY,
            summary,
            details=skipped_reason,
            level="info",
        )
