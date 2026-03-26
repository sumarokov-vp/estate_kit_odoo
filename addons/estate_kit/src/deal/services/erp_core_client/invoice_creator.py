from datetime import datetime
from decimal import Decimal
from typing import Any

from erp_core.core.entities.employee_invoice import EmployeeInvoice
from erp_core.core.entities.invoice import Invoice
from erp_core.core.entities.invoice_status import InvoiceStatusEnum
from erp_core.core.entities.item_invoice import ItemInvoice
from erp_core.infra.postgres.interfaces import (
    IEmployeeInvoiceRepository,
    IInvoiceRepository,
    IInvoiceStatusRepository,
    IItemInvoiceRepository,
)


class InvoiceCreator:
    def __init__(
        self,
        invoice_repository: IInvoiceRepository,
        invoice_status_repository: IInvoiceStatusRepository,
        item_invoice_repository: IItemInvoiceRepository,
        employee_invoice_repository: IEmployeeInvoiceRepository,
    ) -> None:
        self._invoice_repo = invoice_repository
        self._invoice_status_repo = invoice_status_repository
        self._item_invoice_repo = item_invoice_repository
        self._employee_invoice_repo = employee_invoice_repository

    def create_deal_invoice(
        self,
        deal_id: int,
        deal_name: str,
        client_id: int,
        currency_id: int,
        company_party_id: int,
        items: list[dict[str, Any]],
        employees: list[dict[str, Any]],
    ) -> int:
        draft_statuses = self._invoice_status_repo.get_by_name(InvoiceStatusEnum.DRAFT)
        if not draft_statuses:
            raise ValueError("Invoice status 'draft' not found in database")
        draft_status = draft_statuses[0]

        invoice = Invoice(
            client_id=client_id,
            number=f"DEAL-{deal_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            description=f"Сделка: {deal_name}",
            currency_id=currency_id,
            company_party_id=company_party_id,
            status_id=draft_status.id,
            invoice_date=datetime.now(),
        )
        created_invoice = self._invoice_repo.create(invoice)

        for item_data in items:
            item_invoice = ItemInvoice(
                item_id=item_data["item_id"],
                invoice_id=created_invoice.id,
                quantity=Decimal(str(item_data.get("quantity", 1))),
                price=Decimal(str(item_data["price"])),
                discount_amount=Decimal(str(item_data.get("discount_amount", 0))),
            )
            self._item_invoice_repo.create(item_invoice)

        for emp_data in employees:
            employee_invoice = EmployeeInvoice(
                employee_id=emp_data["employee_id"],
                invoice_id=created_invoice.id,
                salary_amount=Decimal(str(emp_data["salary_amount"])),
                currency_id=currency_id,
                type=emp_data.get("type", "commission"),
            )
            self._employee_invoice_repo.create(employee_invoice)

        return created_invoice.id
