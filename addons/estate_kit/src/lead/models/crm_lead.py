import uuid

from odoo import api, fields, models

from ..services.bot_status_checker import BotStatusCheckerService
from ..services.commission import Factory as CommissionFactory
from ..services.deal_creator import Factory as DealCreatorFactory
from ..services.deeplink_builder import DeeplinkBuilderService
from ..services.lead_creator import Factory as LeadCreatorFactory
from ..services.price_estimation import Factory as PriceEstimationFactory


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

    expected_revenue = fields.Monetary(
        string="Expected Revenue",
        compute="_compute_expected_revenue",
        currency_field="company_currency",
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
        checker = BotStatusCheckerService()
        for rec in self:
            rec.bot_connected = checker.is_connected(rec.telegram_user_id)

    @api.depends("lead_code")
    def _compute_deeplink_url(self):
        bot_username = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.customer_bot_username", "")
        )
        builder = DeeplinkBuilderService(bot_username)
        for rec in self:
            rec.deeplink_url = builder.build(rec.lead_code)

    @api.depends("property_id.listing_price", "search_price_min", "search_price_max")
    def _compute_expected_revenue(self):
        commission = CommissionFactory.create(self.env)
        price_estimation = PriceEstimationFactory.create(self.env)
        for rec in self:
            estimated_price = rec._get_estimated_price(price_estimation)
            rate = commission.get_rate(rec)
            rec.expected_revenue = estimated_price * rate / 100

    def _get_estimated_price(self, price_estimation=None) -> float:
        self.ensure_one()
        if self.property_id and self.property_id.listing_price:
            return self.property_id.listing_price
        if self.search_price_min and self.search_price_max:
            return (self.search_price_min + self.search_price_max) / 2
        if self.search_price_min or self.search_price_max:
            return self.search_price_min or self.search_price_max
        if price_estimation:
            return price_estimation.estimate(self)
        return 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") and vals.get("contact_name"):
                vals["name"] = vals["contact_name"]
        records = super().create(vals_list)
        LeadCreatorFactory.create(self.env).after_create(records)
        return records

    def action_set_won(self):
        result = super().action_set_won()
        deal_creator = DealCreatorFactory.create(self.env)
        for lead in self:
            deal_creator.create_if_not_exists(lead)
        return result
