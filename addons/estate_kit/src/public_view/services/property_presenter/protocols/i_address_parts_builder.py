from typing import Protocol


class IAddressPartsBuilder(Protocol):
    def build_parts(self, record, include_district: bool = True) -> list[str]: ...
