from datetime import timedelta

from odoo import fields


class ExpiringNotifier:
    def notify(self, env) -> None:
        today = fields.Date.context_today(env["estate.property.placement"])
        deadline = today + timedelta(days=3)
        expiring = env["estate.property.placement"].search([
            ("state", "=", "active"),
            ("date_end", "!=", False),
            ("date_end", "<=", deadline),
            ("date_end", ">=", today),
        ])
        for placement in expiring:
            prop = placement.property_id
            channel_label = dict(
                placement._fields["channel"].selection
            ).get(placement.channel, placement.channel)
            prop.message_post(
                body=(
                    f"Размещение на канале «{channel_label}» истекает "
                    f"{placement.date_end.strftime('%d.%m.%Y')}. "
                    "Рекомендуется продлить или снять объявление."
                ),
                subject="Размещение скоро истекает",
                message_type="notification",
                subtype_xmlid="mail.mt_note",
                partner_ids=prop.user_id.partner_id.ids if prop.user_id else [],
            )
