from .protocols import IPoolTagFinder


class NoPlacementNotifier:
    def __init__(self, pool_tag_finder: IPoolTagFinder):
        self._pool_tag_finder = pool_tag_finder

    def notify(self, env) -> None:
        pool_tag = self._pool_tag_finder.find(env)
        if not pool_tag:
            return

        pool_properties = env["estate.property"].search([("tag_ids", "in", pool_tag.ids)])
        for prop in pool_properties:
            has_active = any(
                p.state in ("active", "draft") for p in prop.placement_ids
            )
            if not has_active:
                prop.message_post(
                    body=(
                        "Объект в маркетинговом пуле, но нет активных размещений. "
                        "Рекомендуется опубликовать объявление."
                    ),
                    subject="Нет активных размещений",
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=prop.user_id.partner_id.ids if prop.user_id else [],
                )
