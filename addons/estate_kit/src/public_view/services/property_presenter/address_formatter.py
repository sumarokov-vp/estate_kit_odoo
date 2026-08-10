from .protocols import IAddressPartsBuilder


class AddressFormatter:
    def __init__(self, parts_builder: IAddressPartsBuilder) -> None:
        self._parts_builder = parts_builder

    def format(self, prop) -> str:
        parts = self._parts_builder.build_parts(prop, include_district=True)
        return ", ".join(p for p in parts if p)
