from typing import Protocol


class IAddressFieldsValidator(Protocol):
    def require_address_fields(self, vals: dict) -> None: ...
