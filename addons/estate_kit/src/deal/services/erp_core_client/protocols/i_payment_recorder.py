from decimal import Decimal
from typing import Protocol


class IPaymentRecorder(Protocol):
    def record_commission_payment(
        self,
        party_id: int,
        amount: Decimal,
        asset_id: int,
        currency_id: int,
        invoice_id: int | None = None,
        description: str | None = None,
    ) -> int: ...

    def cancel_deal_invoice(self, erp_invoice_id: int) -> None: ...
