from typing import Protocol


class IPromptResolver(Protocol):
    def resolve(self, property_type: str, with_benchmark: bool = False) -> str: ...
