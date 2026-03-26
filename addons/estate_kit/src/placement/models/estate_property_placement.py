from odoo import api, fields, models

from ..services.placement_notifications import Factory as PlacementNotificationsFactory
from ..services.placement_state_machine import Factory as PlacementStateMachineFactory


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

    def action_activate(self):
        PlacementStateMachineFactory.create(self.env).activate(self)

    def action_pause(self):
        PlacementStateMachineFactory.create(self.env).pause(self)

    def action_remove(self):
        PlacementStateMachineFactory.create(self.env).remove(self)

    def action_return_draft(self):
        PlacementStateMachineFactory.create(self.env).return_draft(self)

    @api.model
    def _cron_expire_placements(self):
        PlacementNotificationsFactory.create(self.env).expire_placements()

    @api.model
    def _cron_check_placement_notifications(self):
        PlacementNotificationsFactory.create(self.env).check_notifications()
