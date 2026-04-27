from typing import Protocol


class IPartnerCreator(Protocol):
    def create(self, name: str, phone: str) -> int: ...
