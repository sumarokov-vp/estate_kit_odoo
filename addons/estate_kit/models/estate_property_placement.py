import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EstatePropertyPlacement(models.Model):
    _name = "estate.property.placement"
    _description = "Размещение объекта на рекламном канале"
    _order = "date_start desc, id desc"

    property_id = fields.Many2one(
        "estate.property",
        string="Объект",
        required=True,
        ondelete="cascade",
        index=True,
    )
    channel = fields.Selection(
        [
            ("krysha", "Крыша.kz"),
            ("instagram_organic", "Instagram (пост)"),
            ("instagram_ads", "Instagram (реклама)"),
            ("telegram", "Telegram"),
            ("email", "Email рассылка"),
            ("whatsapp", "WhatsApp"),
            ("other", "Другое"),
        ],
        string="Канал",
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Черновик"),
            ("active", "Активно"),
            ("paused", "Приостановлено"),
            ("expired", "Истекло"),
            ("removed", "Снято"),
        ],
        string="Статус",
        default="draft",
        required=True,
    )
    date_start = fields.Date(string="Дата начала")
    date_end = fields.Date(string="Дата окончания")
    url = fields.Char(string="Ссылка на объявление")
    cost = fields.Monetary(string="Стоимость")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    impressions = fields.Integer(string="Просмотры")
    clicks = fields.Integer(string="Клики")
    leads_count = fields.Integer(string="Лиды")
    notes = fields.Text(string="Комментарий")

    @api.model
    def _cron_expire_placements(self):
        """Expire active placements whose date_end is in the past."""
        today = fields.Date.context_today(self)
        expired = self.search([
            ("state", "=", "active"),
            ("date_end", "!=", False),
            ("date_end", "<", today),
        ])
        expired.write({"state": "expired"})

    @api.model
    def _cron_check_placement_notifications(self):
        """Send placement-related notifications to responsible users."""
        today = fields.Date.context_today(self)
        Property = self.env["estate.property"]
        pool_tag = self.env.ref(
            "estate_kit.property_tag_marketing_pool", raise_if_not_found=False
        )
        if not pool_tag:
            _logger.warning("Tag 'marketing_pool' not found, skipping notifications")
            return

        # 1. Properties in marketing pool with no active placements
        pool_properties = Property.search([("tag_ids", "in", pool_tag.ids)])
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

        # 2. Placements expiring within 3 days
        deadline = today + timedelta(days=3)
        expiring = self.search([
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

        # 3. Properties removed from pool but still have active placements
        non_pool_with_active = Property.search([
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
