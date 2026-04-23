from typing import Protocol


class IAddressParser(Protocol):
    def parse(self, address_title: str) -> tuple[str | None, str | None]: ...
