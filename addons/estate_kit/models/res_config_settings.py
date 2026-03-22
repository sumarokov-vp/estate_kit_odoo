import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)


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

    estate_kit_api_url = fields.Char(
        string="URL API",
        config_parameter="estate_kit.api_url",
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
    def get_yandex_maps_api_key(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.yandex_geocoder_api_key", "")
        )

    def action_register_mls(self):
        self.set_values()
        config = self.env["ir.config_parameter"].sudo()
        company_name = self.estate_kit_reg_company_name
        email = self.estate_kit_reg_email
        phone = self.estate_kit_reg_phone

        client = EstateKitApiClient(self.env)
        if not client.api_url:
            return self._notify("Заполните URL API", "danger")
        if not company_name or not email:
            return self._notify("Заполните название компании и email", "danger")

        payload: dict[str, str] = {"company_name": company_name, "email": email}
        if phone:
            payload["phone"] = phone
        base_url = (config.get_param("web.base.url") or "").replace("http://", "https://")
        if base_url:
            payload["webhook_url"] = f"{base_url}/estatekit/webhook"

        resp = client.post_public("/tenants/register", payload)
        if resp is None:
            return self._notify("Ошибка соединения с API", "danger")
        if resp.status_code not in (200, 201, 202):
            return self._notify(f"Ошибка API: {resp.status_code} {resp.text[:200]}", "danger")

        data = resp.json()
        _logger.info("MLS register response: status_code=%s, data=%s", resp.status_code, data)
        request_code = data.get("request_code", "")
        status = data.get("status", "pending")

        config.set_param("estate_kit.reg_request_code", request_code)
        config.set_param("estate_kit.reg_status", status)

        return self._reload_settings()

    def action_check_registration_status(self):
        config = self.env["ir.config_parameter"].sudo()
        request_code = config.get_param("estate_kit.reg_request_code") or ""
        email = config.get_param("estate_kit.reg_email") or ""
        current_status = config.get_param("estate_kit.reg_status") or ""

        client = EstateKitApiClient(self.env)
        if not request_code:
            return self._notify("Нет данных для проверки", "danger")

        if current_status == "pending_update":
            if not client.is_configured:
                return self._notify("API не настроен (нет URL или API-ключа)", "danger")
            endpoint = f"/tenants/update/{request_code}"
            resp = client.get_raw(endpoint)
        else:
            if not client.api_url or not email:
                return self._notify("Нет данных для проверки", "danger")
            endpoint = f"/tenants/register/{request_code}"
            resp = client.get_public(endpoint, params={"email": email})

        if resp is None:
            return self._notify("Ошибка соединения с API", "danger")
        if resp.status_code == 404:
            config.set_param("estate_kit.reg_request_code", "")
            config.set_param("estate_kit.reg_status", "")
            return self._reload_settings()
        if resp.status_code != 200:
            return self._notify(f"Ошибка API: {resp.status_code}", "danger")

        data = resp.json()
        status = data.get("status", "unknown")

        if status == "approved":
            if current_status != "pending_update":
                if data.get("api_key"):
                    config.set_param("estate_kit.api_key", data["api_key"])
                if data.get("webhook_secret"):
                    config.set_param("estate_kit.webhook_secret", data["webhook_secret"])
            config.set_param("estate_kit.reg_request_code", "")
            config.set_param("estate_kit.reg_status", "")
        else:
            config.set_param("estate_kit.reg_status", status)

        return self._reload_settings()

    def action_update_tenant_data(self):
        self.set_values()
        config = self.env["ir.config_parameter"].sudo()

        client = EstateKitApiClient(self.env)
        if not client.is_configured:
            return self._notify("API не настроен (нет URL или API-ключа)", "danger")

        payload: dict[str, str] = {}
        company_name = self.estate_kit_reg_company_name
        phone = self.estate_kit_reg_phone
        if company_name:
            payload["company_name"] = company_name
        if phone:
            payload["phone"] = phone
        base_url = (config.get_param("web.base.url") or "").replace("http://", "https://")
        if base_url:
            payload["webhook_url"] = f"{base_url}/estatekit/webhook"

        resp = client.post_raw("/tenants/update", payload)
        if resp is None:
            return self._notify("Ошибка соединения с API", "danger")
        if resp.status_code == 404:
            return self._notify("Активная подписка не найдена", "warning")
        if resp.status_code == 422:
            return self._notify("Нет полей для обновления", "warning")
        if resp.status_code == 200:
            return self._notify("Данные совпадают, изменений нет", "info")
        if resp.status_code == 202:
            data = resp.json()
            request_code = data.get("request_code", "")
            config.set_param("estate_kit.reg_request_code", request_code)
            config.set_param("estate_kit.reg_status", "pending_update")
            return self._reload_settings()

        return self._notify(f"Ошибка API: {resp.status_code} {resp.text[:200]}", "danger")

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
