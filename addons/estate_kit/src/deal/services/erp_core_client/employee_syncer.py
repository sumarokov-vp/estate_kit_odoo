from erp_core.party.entities.employee import Employee
from erp_core.party.entities.party import Party
from erp_core.party.protocols.employee_repository import IEmployeeRepository
from erp_core.party.protocols.party_repository import IPartyRepository


class EmployeeSyncer:
    def __init__(
        self,
        employee_repository: IEmployeeRepository,
        party_repository: IPartyRepository,
    ) -> None:
        self._employee_repo = employee_repository
        self._party_repo = party_repository

    def ensure_employee(self, odoo_user_id: int, name: str) -> int:
        external_id = str(odoo_user_id)
        existing = self._employee_repo.find_by_external_id(external_id)
        if existing:
            return existing.party_id

        party = self._party_repo.create(
            Party(name=name, party_type="employee")
        )
        employee = self._employee_repo.create(
            Employee(
                party_id=party.id,
                external_id=external_id,
                currency_id=1,
            )
        )
        return employee.party_id

    def ensure_party(
        self,
        odoo_partner_id: int,
        name: str,
        party_type: str,
    ) -> int:
        odoo_tax_id = f"ODOO_PARTNER_{odoo_partner_id}"
        existing = self._party_repo.find_by_tax_id(odoo_tax_id)
        if existing:
            return existing.id

        party = self._party_repo.create(
            Party(
                name=name,
                party_type=party_type,
                tax_id=odoo_tax_id,
            )
        )
        return party.id
