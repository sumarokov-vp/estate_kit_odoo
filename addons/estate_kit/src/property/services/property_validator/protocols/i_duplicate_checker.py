from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..duplicate_checker import DuplicateCheckResult


class IDuplicateChecker(Protocol):
    def check(self, vals: dict, exclude_id: int = 0) -> DuplicateCheckResult | None: ...
