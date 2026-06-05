from typing import Protocol


class ISectionsBuilder(Protocol):
    def build(self, prop) -> list[dict]: ...
