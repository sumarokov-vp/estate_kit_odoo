import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info(
        "Market snapshot models and hedonic config parameters will be created via manifest.",
    )
