from typing import Protocol


class IActivePropertiesLoader(Protocol):
    def load(self): ...
