from typing import Protocol


class IPromptResolver(Protocol):
    def resolve(self, property_type: str) -> str: ...
