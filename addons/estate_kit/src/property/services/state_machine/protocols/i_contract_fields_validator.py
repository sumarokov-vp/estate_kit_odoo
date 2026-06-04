from typing import Protocol


class IContractFieldsValidator(Protocol):
    def validate(self, records) -> None: ...
