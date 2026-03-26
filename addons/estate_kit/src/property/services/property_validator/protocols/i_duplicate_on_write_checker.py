from typing import Protocol


class IDuplicateOnWriteChecker(Protocol):
    def check_duplicate_on_write(self, records, vals: dict) -> None: ...
