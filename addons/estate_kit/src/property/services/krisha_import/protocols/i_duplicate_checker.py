from typing import Protocol


class IDuplicateChecker(Protocol):
    def is_imported(self, krisha_url: str) -> bool: ...
