from decimal import Decimal

from erp_core.core.entities.invoice import Invoice
from erp_core.core.entities.money import Money, MoneyDirection, SubmittingType
from erp_core.infra.postgres.interfaces import (
    IInvoiceRepository,
    IInvoiceStatusRepository,
    IMoneyRepository,
    IMoneyStatusRepository,
)


class PaymentRecorder:
    def __init__(
        self,
        money_repository: IMoneyRepository,
        money_status_repository: IMoneyStatusRepository,
        invoice_repository: IInvoiceRepository,
        invoice_status_repository: IInvoiceStatusRepository,
    ) -> None:
        self._money_repo = money_repository
        self._money_status_repo = money_status_repository
        self._invoice_repo = invoice_repository
        self._invoice_status_repo = invoice_status_repository

    def record_commission_payment(
        self,
        party_id: int,
        amount: Decimal,
        asset_id: int,
        currency_id: int,
        invoice_id: int | None = None,
        description: str | None = None,
    ) -> int:
        submitted_statuses = self._money_status_repo.get_by_name("submitted")
        if not submitted_statuses:
            raise ValueError("Money status 'submitted' not found in database")
        submitted_status = submitted_statuses[0]

        money = Money(
            invoice_id=invoice_id,
            party_id=party_id,
            asset_id=asset_id,
            amount=amount,
            currency_id=currency_id,
            status_id=submitted_status.id,
            direction=MoneyDirection.OUT.value,
            description=description,
            submitting_type=SubmittingType.MUTUAL,
        )
        created_money = self._money_repo.create(money)
        return created_money.id

    def cancel_deal_invoice(self, erp_invoice_id: int) -> None:
        invoice = self._invoice_repo.get_by_id(erp_invoice_id)
        cancelled_statuses = self._invoice_status_repo.get_by_name("cancelled")
        if not cancelled_statuses:
            raise ValueError("Invoice status 'cancelled' not found in database")
        cancelled_status = cancelled_statuses[0]
        invoice.status_id = cancelled_status.id
        self._invoice_repo.update(invoice)
