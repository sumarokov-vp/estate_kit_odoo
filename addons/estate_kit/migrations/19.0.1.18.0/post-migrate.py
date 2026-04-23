import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        DELETE FROM ir_cron
        WHERE cron_name = 'Daily market snapshot collection from Krisha'
        """
    )
    _logger.info(
        "Removed obsolete market snapshot cron (moved to krisha_snapshots sidecar)"
    )

    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'estate_kit'
          AND name LIKE 'market_snapshot_cron%%'
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'estate_kit'
          AND name = 'cron_collect_market_snapshots'
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'estate_kit'
          AND name = 'action_collect_snapshots_now'
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'estate_kit'
          AND name = 'estate_menu_market_collect_now'
        """
    )
