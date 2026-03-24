import uuid

from odoo import api, fields, models


def _short_uuid():
    return uuid.uuid4().hex[:12]


class CrmLead(models.Model):
    _inherit = "crm.lead"

    property_id = fields.Many2one(
        "estate.property",
        string="Property",
        help="Related property for this deal",
    )
    isa_user_id = fields.Many2one(
        "res.users",
        string="ISA",
        help="Inside Sales Agent who qualified the lead",
    )
    buyer_agent_id = fields.Many2one(
        "res.users",
        string="Buyer's Agent",
    )
    transaction_coordinator_id = fields.Many2one(
        "res.users",
        string="Transaction Coordinator",
    )

    # === Потребность клиента ===
    search_deal_type = fields.Selection(
        [("sale", "Покупка"), ("rent", "Аренда")],
        string="Тип сделки",
    )
    search_property_type = fields.Selection(
        [
            ("apartment", "Квартира"),
            ("house", "Дом"),
            ("townhouse", "Таунхаус"),
            ("commercial", "Коммерция"),
            ("land", "Земля"),
        ],
        string="Тип объекта",
    )
    search_city_id = fields.Many2one(
        "estate.city",
        string="Город",
        ondelete="set null",
    )
    search_district_ids = fields.Many2many(
        "estate.district",
        "crm_lead_estate_district_rel",
        "lead_id",
        "district_id",
        string="Районы",
    )
    search_rooms_min = fields.Integer(string="Комнат от")
    search_rooms_max = fields.Integer(string="Комнат до")
    search_price_min = fields.Monetary(string="Цена от", currency_field="company_currency")
    search_price_max = fields.Monetary(string="Цена до", currency_field="company_currency")
    search_area_min = fields.Float(string="Площадь от, м²", digits=(10, 1))
    search_area_max = fields.Float(string="Площадь до, м²", digits=(10, 1))
    search_notes = fields.Text(string="Примечания по поиску")

    company_currency = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Валюта компании",
        readonly=True,
    )

    # === Deeplink и Telegram ===
    lead_code = fields.Char(
        string="Код лида",
        default=lambda self: _short_uuid(),
        readonly=True,
        copy=False,
    )
    telegram_user_id = fields.Char(
        string="Telegram User ID",
        help="ID пользователя Telegram (заполняется при переходе по deeplink)",
        copy=False,
    )
    bot_connected = fields.Boolean(
        string="Бот подключён",
        compute="_compute_bot_connected",
        store=True,
    )
    last_bot_activity = fields.Datetime(
        string="Последняя активность в боте",
        readonly=True,
        copy=False,
    )
    deeplink_url = fields.Char(
        string="Deeplink URL",
        compute="_compute_deeplink_url",
    )

    _sql_constraints = [
        ("lead_code_unique", "UNIQUE(lead_code)", "Код лида должен быть уникальным"),
    ]

    @api.depends("telegram_user_id")
    def _compute_bot_connected(self):
        for rec in self:
            rec.bot_connected = bool(rec.telegram_user_id)

    @api.depends("lead_code")
    def _compute_deeplink_url(self):
        bot_username = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.customer_bot_username", "")
        )
        for rec in self:
            if bot_username and rec.lead_code:
                rec.deeplink_url = f"https://t.me/{bot_username}?start=lead_{rec.lead_code}"
            else:
                rec.deeplink_url = False

    # === Автосоздание сделки ===

    def action_set_won(self):
        result = super().action_set_won()
        for lead in self:
            lead._create_deal_if_not_exists()
        return result

    def _create_deal_if_not_exists(self):
        if self.env["estate.deal"].search([("lead_id", "=", self.id)], limit=1):
            return

        deal_type = self.search_deal_type or "sale"
        deal = self.env["estate.deal"].create({
            "lead_id": self.id,
            "property_id": self.property_id.id or False,
            "client_partner_id": self.partner_id.id or False,
            "deal_type": deal_type,
        })
        self._create_deal_participants(deal)

    def _create_deal_participants(self, deal):
        participants = []
        if self.isa_user_id:
            participants.append({"deal_id": deal.id, "role": "isa", "user_id": self.isa_user_id.id})
        if self.buyer_agent_id:
            participants.append({"deal_id": deal.id, "role": "buyer_agent", "user_id": self.buyer_agent_id.id})
        if self.transaction_coordinator_id:
            participants.append({"deal_id": deal.id, "role": "coordinator", "user_id": self.transaction_coordinator_id.id})
        if participants:
            self.env["estate.deal.participant"].create(participants)
