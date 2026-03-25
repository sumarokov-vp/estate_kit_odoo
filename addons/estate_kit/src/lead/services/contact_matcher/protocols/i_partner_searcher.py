from typing import Protocol


class IPartnerSearcher(Protocol):
    def find_by_phone(self, phone: str | None) -> int | None: ...
