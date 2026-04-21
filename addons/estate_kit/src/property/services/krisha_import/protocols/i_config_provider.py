from typing import Protocol

from ..config import KrishaImportConfig


class IConfigProvider(Protocol):
    def load(self) -> KrishaImportConfig: ...
