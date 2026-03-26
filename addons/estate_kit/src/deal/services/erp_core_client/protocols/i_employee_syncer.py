from typing import Protocol


class IEmployeeSyncer(Protocol):
    def ensure_employee(self, odoo_user_id: int, name: str) -> int: ...

    def ensure_party(
        self,
        odoo_partner_id: int,
        name: str,
        party_type: str,
    ) -> int: ...
