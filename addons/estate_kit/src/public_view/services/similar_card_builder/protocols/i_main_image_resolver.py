from typing import Protocol


class IMainImageResolver(Protocol):
    def resolve(self, prop): ...
