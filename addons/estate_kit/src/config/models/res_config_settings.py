from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..services.mls_registration import MlsRegistrationFactory


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    estate_kit_reg_company_name = fields.Char(
        string="Название компании",
        config_parameter="estate_kit.reg_company_name",
    )
    estate_kit_reg_email = fields.Char(
        string="Email",
        config_parameter="estate_kit.reg_email",
    )
    estate_kit_reg_phone = fields.Char(
        string="Телефон",
        config_parameter="estate_kit.reg_phone",
    )
    estate_kit_reg_request_code = fields.Char(
        string="Код заявки",
        config_parameter="estate_kit.reg_request_code",
        readonly=True,
    )
    estate_kit_reg_status = fields.Char(
        string="Статус регистрации",
        config_parameter="estate_kit.reg_status",
        readonly=True,
    )

    estate_kit_customer_bot_username = fields.Char(
        string="Username бота клиентов",
        config_parameter="estate_kit.customer_bot_username",
        help="Username Telegram-бота для клиентов (без @). Используется для генерации Deeplink URL в лидах.",
    )

    estate_kit_api_url = fields.Char(
        string="URL API",
        config_parameter="estate_kit.api_url",
    )
    estate_kit_twogis_api_key = fields.Char(
        string="API-ключ 2GIS",
        config_parameter="estate_kit.twogis_api_key",
        help="API-ключ 2GIS для карт и геокодирования",
    )

    estate_kit_anthropic_api_key = fields.Char(
        string="API-ключ Anthropic",
        config_parameter="estate_kit.anthropic_api_key",
    )
    estate_kit_anthropic_model = fields.Char(
        string="Модель Anthropic",
        config_parameter="estate_kit.anthropic_model",
    )
    estate_kit_is_registered = fields.Boolean(
        string="Зарегистрирован",
        compute="_compute_is_registered",
    )

    # === Маркетинговый пул ===
    estate_kit_pool_max_size = fields.Integer(
        string="Размер пула",
        config_parameter="estate_kit.pool_max_size",
        default=100,
        help="Максимальное количество объектов в маркетинговом пуле. "
             "Если подходящих объектов меньше — в пуле будет столько, сколько набралось.",
    )
    estate_kit_pool_min_price_score = fields.Integer(
        string="Мин. Price Score",
        config_parameter="estate_kit.pool_min_price_score",
        default=3,
        help="Минимальный балл конкурентности цены (1–10). "
             "Объект ниже порога не попадает в пул.",
    )
    estate_kit_pool_min_quality_score = fields.Integer(
        string="Мин. Quality Score",
        config_parameter="estate_kit.pool_min_quality_score",
        default=3,
        help="Минимальный балл качества объекта (1–10). "
             "Объект ниже порога не попадает в пул.",
    )
    estate_kit_pool_min_listing_score = fields.Integer(
        string="Мин. Listing Score",
        config_parameter="estate_kit.pool_min_listing_score",
        default=3,
        help="Минимальный балл качества карточки (1–10). "
             "Объект ниже порога не попадает в пул.",
    )
    estate_kit_pool_inclusion_threshold = fields.Float(
        string="Порог включения",
        config_parameter="estate_kit.pool_inclusion_threshold",
        default=7.0,
        digits=(4, 1),
        help="Минимальный Marketing Pool Score (MPS) для автоматического включения объекта в пул. "
             "Должен быть выше порога исключения для создания зоны гистерезиса.",
    )
    estate_kit_pool_exclusion_threshold = fields.Float(
        string="Порог исключения",
        config_parameter="estate_kit.pool_exclusion_threshold",
        default=4.0,
        digits=(4, 1),
        help="MPS ниже этого значения приводит к исключению объекта из пула. "
             "Разница с порогом включения создаёт гистерезис — предотвращает частое включение/исключение.",
    )
    estate_kit_pool_scoring_weight = fields.Float(
        string="Вес скоринга",
        config_parameter="estate_kit.pool_scoring_weight",
        default=0.6,
        digits=(3, 2),
        help="Вес AI-скоринга в формуле MPS. Сумма с весом тир-листов должна равняться 1.0.",
    )
    estate_kit_pool_tier_weight = fields.Float(
        string="Вес тир-листов",
        config_parameter="estate_kit.pool_tier_weight",
        default=0.4,
        digits=(3, 2),
        help="Вес тир-листов в формуле MPS. Сумма с весом скоринга должна равняться 1.0.",
    )

    # === Комиссия ===
    estate_kit_min_commission_percent = fields.Float(
        string="Минимальная комиссия, %",
        config_parameter="estate_kit.min_commission_percent",
        digits=(5, 2),
        help="Минимальная комиссия агентства (%)",
    )
    estate_kit_max_discount_percent = fields.Float(
        string="Макс. скидка от listing_price, %",
        config_parameter="estate_kit.max_discount_percent",
        default=10.0,
        digits=(5, 2),
        help="Допустимый коридор снижения цены сделки от listing_price (%)",
    )

    # === Парсинг Krisha.kz ===
    estate_kit_krisha_search_url = fields.Char(
        string="URL поиска Krisha.kz",
        config_parameter="estate_kit.krisha_search_url",
        help="URL поиска на Krisha.kz с фильтрами. Фоновая задача импортирует объекты, "
             "найденные по этой ссылке. Пустое значение отключает импорт.",
    )
    estate_kit_krisha_import_limit = fields.Integer(
        string="Максимум объектов за запуск",
        config_parameter="estate_kit.krisha_import_limit",
        default=10,
        help="Максимум объектов за один запуск фоновой задачи.",
    )

    @api.constrains("estate_kit_pool_scoring_weight", "estate_kit_pool_tier_weight")
    def _check_pool_weights_sum(self):
        for rec in self:
            w_scoring = rec.estate_kit_pool_scoring_weight or 0.0
            w_tier = rec.estate_kit_pool_tier_weight or 0.0
            if abs((w_scoring + w_tier) - 1.0) > 0.01:
                raise ValidationError(
                    "Сумма весов скоринга и тир-листов должна равняться 1.0 "
                    "(сейчас: %.2f + %.2f = %.2f)" % (w_scoring, w_tier, w_scoring + w_tier)
                )

    @api.depends("estate_kit_api_url")
    def _compute_is_registered(self):
        api_key = self.env["ir.config_parameter"].sudo().get_param("estate_kit.api_key") or ""
        for rec in self:
            rec.estate_kit_is_registered = bool(api_key)

    @api.model
    def get_twogis_api_key(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.twogis_api_key", "")
        )

    def action_register_mls(self):
        self.set_values()
        return MlsRegistrationFactory.create(self.env).register(self)

    def action_check_registration_status(self):
        return MlsRegistrationFactory.create(self.env).check_status(self)

    def action_update_tenant_data(self):
        self.set_values()
        return MlsRegistrationFactory.create(self.env).update_data(self)

    def action_import_krisha_now(self):
        self.set_values()
        self.env.ref("estate_kit.cron_krisha_import_manual").sudo()._trigger()
        return self._notify(
            "Импорт запущен в фоне. Прогресс смотри в логах Odoo."
        )

    def _notify(self, message, notification_type="info"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": notification_type,
                "sticky": False,
            },
        }

    def _reload_settings(self):
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
