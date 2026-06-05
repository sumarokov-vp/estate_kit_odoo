from typing import Protocol

from ..result import SingleImportResult


class ISingleItemImporter(Protocol):
    def import_one(self, url: str) -> SingleImportResult: ...
