import logging
from pathlib import Path

from erp_core.shared.migrations import apply_migrations

from ...config import get_database_url

_logger = logging.getLogger(__name__)

_CLIENT_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


class Initializer:
    def initialize(self) -> None:
        url = get_database_url()
        applied = apply_migrations(url, _CLIENT_MIGRATIONS_DIR)
        _logger.info("ERP Core: applied %d migrations", applied)
