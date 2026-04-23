from contextlib import AbstractContextManager
from typing import Protocol


class ITransactionScope(Protocol):
    def savepoint(self) -> AbstractContextManager[None]: ...

    def commit(self) -> None: ...
