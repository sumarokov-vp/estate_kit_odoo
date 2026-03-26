from typing import Protocol


class IImageDeleter(Protocol):
    def delete(self, records) -> None: ...
