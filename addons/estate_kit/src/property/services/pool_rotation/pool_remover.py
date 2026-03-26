import logging

_logger = logging.getLogger(__name__)


class PoolRemover:
    def remove(self, prop, pool_tag, reason: str) -> None:
        prop.tag_ids -= pool_tag
        active_placements = prop.placement_ids.filtered(
            lambda p: p.state in ("draft", "active", "paused")
        )
        if active_placements:
            active_placements.write({"state": "removed"})
        prop.message_post(
            body="Выведен из маркетингового пула: %s" % reason,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        _logger.info("Property %s removed from pool: %s", prop.id, reason)
