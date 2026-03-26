from .protocols import IPoolTagFinder


class OrphanPlacementNotifier:
    def __init__(self, pool_tag_finder: IPoolTagFinder):
        self._pool_tag_finder = pool_tag_finder

    def notify(self, env) -> None:
        pool_tag = self._pool_tag_finder.find(env)
        if not pool_tag:
            return

        non_pool_with_active = env["estate.property"].search([
            ("tag_ids", "not in", pool_tag.ids),
            ("placement_ids.state", "=", "active"),
        ])
        for prop in non_pool_with_active:
            active_channels = [
                dict(p._fields["channel"].selection).get(p.channel, p.channel)
                for p in prop.placement_ids
                if p.state == "active"
            ]
            if active_channels:
                channels_str = ", ".join(active_channels)
                prop.message_post(
                    body=(
                        "Объект не в маркетинговом пуле, но есть активные "
                        f"размещения: {channels_str}. "
                        "Рекомендуется снять объявления."
                    ),
                    subject="Активные размещения вне пула",
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=prop.user_id.partner_id.ids if prop.user_id else [],
                )
