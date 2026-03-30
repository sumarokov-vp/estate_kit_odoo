from datetime import datetime
from decimal import Decimal

from erp_core.mutual.protocols.mutual_repository import IMutualRepository


class BalanceProvider:
    def __init__(
        self,
        mutual_repository: IMutualRepository,
    ) -> None:
        self._mutual_repo = mutual_repository

    def get_party_balance(self, party_id: int) -> Decimal:
        return self._mutual_repo.get_cumulative_total_by_party_id(
            party_id=party_id,
            up_to_date=datetime.now(),
        )

    def get_employee_commissions(
        self,
        employee_party_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> Decimal:
        salary_rows = self._mutual_repo.get_salary_accruals_by_party_and_date(
            party_id=employee_party_id,
            from_date=date_from,
            to_date=date_to,
        )
        return sum((row.amount for row in salary_rows), Decimal("0"))
