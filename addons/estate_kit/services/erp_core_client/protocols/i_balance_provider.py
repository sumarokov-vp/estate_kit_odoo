from datetime import datetime
from decimal import Decimal
from typing import Protocol


class IBalanceProvider(Protocol):
    def get_party_balance(self, party_id: int) -> Decimal: ...

    def get_employee_commissions(
        self,
        employee_party_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> Decimal: ...
