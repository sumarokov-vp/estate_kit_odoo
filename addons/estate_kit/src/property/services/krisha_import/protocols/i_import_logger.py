from typing import Any, Protocol


class IImportLogger(Protocol):
    def log_success(self, url: str, property_id: int, detail: dict[str, Any]) -> None: ...

    def log_duplicate(self, url: str) -> None: ...

    def log_error(self, url: str, exc: BaseException) -> None: ...

    def log_summary(
        self,
        imported: int,
        duplicates: int,
        errors: int,
        skipped_reason: str | None = None,
    ) -> None: ...
