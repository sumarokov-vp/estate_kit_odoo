from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class KrishaImportResult:
    imported: int
    duplicates: int
    errors: int
    skipped_reason: str | None = None


class SingleImportStatus(str, Enum):
    IMPORTED = "imported"
    DUPLICATE = "duplicate"
    ERROR = "error"


@dataclass(frozen=True)
class SingleImportResult:
    status: SingleImportStatus
    url: str
    property_id: int | None = None
    error_message: str | None = None

    @property
    def is_imported(self) -> bool:
        return self.status is SingleImportStatus.IMPORTED

    @property
    def is_duplicate(self) -> bool:
        return self.status is SingleImportStatus.DUPLICATE

    @property
    def is_error(self) -> bool:
        return self.status is SingleImportStatus.ERROR
