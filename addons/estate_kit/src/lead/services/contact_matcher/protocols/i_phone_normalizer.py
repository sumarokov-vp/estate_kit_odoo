from typing import Protocol


class IPhoneNormalizer(Protocol):
    def normalize(self, phone: str | None) -> str: ...
