import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        "SELECT value FROM ir_config_parameter WHERE key = 'estate_kit.yandex_geocoder_api_key'"
    )
    row = cr.fetchone()
    yandex_value = (row[0] if row else "") or ""

    if yandex_value:
        cr.execute(
            "SELECT value FROM ir_config_parameter WHERE key = 'estate_kit.twogis_api_key'"
        )
        row = cr.fetchone()
        twogis_value = (row[0] if row else "") or ""
        if not twogis_value:
            cr.execute(
                "UPDATE ir_config_parameter SET value = %s WHERE key = 'estate_kit.twogis_api_key'",
                (yandex_value,),
            )
            _logger.info(
                "Copied yandex_geocoder_api_key value into twogis_api_key "
                "(twogis key was empty). Verify the key is a valid 2GIS API key.",
            )

    cr.execute(
        "DELETE FROM ir_config_parameter WHERE key = 'estate_kit.yandex_geocoder_api_key'"
    )
    _logger.info("Removed obsolete estate_kit.yandex_geocoder_api_key parameter")
