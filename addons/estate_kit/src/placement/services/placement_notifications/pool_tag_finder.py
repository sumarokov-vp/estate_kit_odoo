import logging

_logger = logging.getLogger(__name__)

_POOL_TAG_XML_ID = "estate_kit.property_tag_marketing_pool"


class PoolTagFinder:
    def find(self, env):
        tag = env.ref(_POOL_TAG_XML_ID, raise_if_not_found=False)
        if not tag:
            _logger.warning("Tag 'marketing_pool' not found, skipping notifications")
        return tag
