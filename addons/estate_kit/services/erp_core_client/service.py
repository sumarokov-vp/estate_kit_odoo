from datetime import datetime
from decimal import Decimal
from typing import Any

from .protocols import IInvoiceCreator, IPaymentRecorder, IBalanceProvider, IEmployeeSyncer


class ErpCoreClientService:
    def __init__(
        self,
        invoice_creator: IInvoiceCreator,
        payment_recorder: IPaymentRecorder,
        balance_provider: IBalanceProvider,
        employee_syncer: IEmployeeSyncer,
    ) -> None:
        self._invoice_creator = invoice_creator
        self._payment_recorder = payment_recorder
        self._balance_provider = balance_provider
        self._employee_syncer = employee_syncer

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
        return self._invoice_creator.create_deal_invoice(
            deal_id=deal_id,
            deal_name=deal_name,
            client_id=client_id,
            currency_id=currency_id,
            company_party_id=company_party_id,
            items=items,
            employees=employees,
        )

    def record_commission_payment(
        self,
        party_id: int,
        amount: Decimal,
        asset_id: int,
        currency_id: int,
        invoice_id: int | None = None,
        description: str | None = None,
    ) -> int:
        return self._payment_recorder.record_commission_payment(
            party_id=party_id,
            amount=amount,
            asset_id=asset_id,
            currency_id=currency_id,
            invoice_id=invoice_id,
            description=description,
        )

    def get_party_balance(self, party_id: int) -> Decimal:
        return self._balance_provider.get_party_balance(party_id=party_id)

    def get_employee_commissions(
        self,
        employee_party_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> Decimal:
        return self._balance_provider.get_employee_commissions(
            employee_party_id=employee_party_id,
            date_from=date_from,
            date_to=date_to,
        )

    def cancel_deal_invoice(self, erp_invoice_id: int) -> None:
        self._payment_recorder.cancel_deal_invoice(erp_invoice_id=erp_invoice_id)

    def ensure_employee(self, odoo_user_id: int, name: str) -> int:
        return self._employee_syncer.ensure_employee(odoo_user_id=odoo_user_id, name=name)

    def ensure_party(
        self,
        odoo_partner_id: int,
        name: str,
        party_type: str,
    ) -> int:
        return self._employee_syncer.ensure_party(
            odoo_partner_id=odoo_partner_id,
            name=name,
            party_type=party_type,
        )
