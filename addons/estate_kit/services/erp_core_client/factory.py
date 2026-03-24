from erp_core.infra.postgres.employee_repository import EmployeeRepository
from erp_core.infra.postgres.invoice_repository import InvoiceRepository
from erp_core.infra.postgres.invoice_status_repository import InvoiceStatusRepository
from erp_core.infra.postgres.item_invoice_repository import ItemInvoiceRepository
from erp_core.infra.postgres.employee_invoice_repository import EmployeeInvoiceRepository
from erp_core.infra.postgres.money_repository import MoneyRepository
from erp_core.infra.postgres.money_status_repository import MoneyStatusRepository
from erp_core.infra.postgres.mutual_repository import MutualRepository
from erp_core.infra.postgres.party_repository import PartyRepository

from .balance_provider import BalanceProvider
from .config import get_database_url
from .employee_syncer import EmployeeSyncer
from .invoice_creator import InvoiceCreator
from .payment_recorder import PaymentRecorder
from .service import ErpCoreClientService


class Factory:
    @staticmethod
    def create() -> ErpCoreClientService:
        database_url = get_database_url()

        invoice_repo = InvoiceRepository(database_url)
        invoice_status_repo = InvoiceStatusRepository(database_url)
        item_invoice_repo = ItemInvoiceRepository(database_url)
        employee_invoice_repo = EmployeeInvoiceRepository(database_url)
        money_repo = MoneyRepository(database_url)
        money_status_repo = MoneyStatusRepository(database_url)
        mutual_repo = MutualRepository(database_url)
        employee_repo = EmployeeRepository(database_url)
        party_repo = PartyRepository(database_url)

        invoice_creator = InvoiceCreator(
            invoice_repository=invoice_repo,
            invoice_status_repository=invoice_status_repo,
            item_invoice_repository=item_invoice_repo,
            employee_invoice_repository=employee_invoice_repo,
        )
        payment_recorder = PaymentRecorder(
            money_repository=money_repo,
            money_status_repository=money_status_repo,
            invoice_repository=invoice_repo,
            invoice_status_repository=invoice_status_repo,
        )
        balance_provider = BalanceProvider(
            mutual_repository=mutual_repo,
        )
        employee_syncer = EmployeeSyncer(
            employee_repository=employee_repo,
            party_repository=party_repo,
        )

        return ErpCoreClientService(
            invoice_creator=invoice_creator,
            payment_recorder=payment_recorder,
            balance_provider=balance_provider,
            employee_syncer=employee_syncer,
        )
