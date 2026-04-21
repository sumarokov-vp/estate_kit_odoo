from dataclasses import dataclass


@dataclass(frozen=True)
class KrishaImportConfig:
    search_url: str
    limit: int
