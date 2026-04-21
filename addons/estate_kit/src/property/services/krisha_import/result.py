from dataclasses import dataclass


@dataclass(frozen=True)
class KrishaImportResult:
    imported: int
    duplicates: int
    errors: int
    skipped_reason: str | None = None
