from decimal import Decimal
from typing import Any, Protocol


class IInvoiceCreator(Protocol):
    def create_deal_invoice(
        self,
        deal_id: int,
        deal_name: str,
        client_id: int,
        currency_id: int,
        company_party_id: int,
        items: list[dict[str, Any]],
        employees: list[dict[str, Any]],
    ) -> int: ...
