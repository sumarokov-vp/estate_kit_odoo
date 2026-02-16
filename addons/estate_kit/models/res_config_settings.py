import logging

import requests

from odoo import fields, models

from ..services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)

WEBHOOK_EVENTS = [
    "property.transition.*",
    "property.locked",
    "property.unlocked",
    "mls.new_listing",
    "mls.listing_updated",
    "mls.listing_removed",
    "contact_request.received",
]


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
    estate_kit_api_key = fields.Char(
        string="API-ключ",
        config_parameter="estate_kit.api_key",
    )
    estate_kit_webhook_secret = fields.Char(
        string="Webhook Secret",
        config_parameter="estate_kit.webhook_secret",
    )
    estate_kit_webhook_url = fields.Char(
        string="Webhook URL",
        config_parameter="estate_kit.webhook_url",
    )

    def action_register_mls(self):
        config = self.env["ir.config_parameter"].sudo()
        api_url = config.get_param("estate_kit.api_url") or ""
        company_name = self.estate_kit_reg_company_name
        email = self.estate_kit_reg_email
        phone = self.estate_kit_reg_phone

        if not api_url:
            return self._notify("Заполните URL API", "danger")
        if not company_name or not email:
            return self._notify("Заполните название компании и email", "danger")

        url = f"{api_url.rstrip('/')}/tenants/register"
        payload = {"company_name": company_name, "email": email}
        if phone:
            payload["phone"] = phone

        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code not in (200, 201):
            return self._notify(f"Ошибка API: {resp.status_code} {resp.text[:200]}", "danger")

        data = resp.json()
        request_code = data.get("request_code", "")
        status = data.get("status", "pending")

        config.set_param("estate_kit.reg_request_code", request_code)
        config.set_param("estate_kit.reg_status", status)
        config.set_param("estate_kit.reg_company_name", company_name)
        config.set_param("estate_kit.reg_email", email)
        if phone:
            config.set_param("estate_kit.reg_phone", phone)

        return self._notify("Заявка отправлена", "success")

    def action_check_registration_status(self):
        config = self.env["ir.config_parameter"].sudo()
        api_url = config.get_param("estate_kit.api_url") or ""
        request_code = config.get_param("estate_kit.reg_request_code") or ""
        email = config.get_param("estate_kit.reg_email") or ""

        if not api_url or not request_code or not email:
            return self._notify("Нет данных для проверки", "danger")

        url = f"{api_url.rstrip('/')}/tenants/register/{request_code}"
        resp = requests.get(url, params={"email": email}, timeout=15)
        if resp.status_code != 200:
            return self._notify(f"Ошибка API: {resp.status_code}", "danger")

        data = resp.json()
        status = data.get("status", "unknown")
        config.set_param("estate_kit.reg_status", status)

        if status == "approved" and data.get("api_key"):
            config.set_param("estate_kit.api_key", data["api_key"])
            return self._notify("Регистрация одобрена! API-ключ сохранён.", "success")

        status_labels = {"pending": "На рассмотрении", "approved": "Одобрена", "rejected": "Отклонена"}
        label = status_labels.get(status, status)
        return self._notify(f"Статус: {label}", "info")

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

    def set_values(self):
        config = self.env["ir.config_parameter"].sudo()
        old_url = config.get_param("estate_kit.webhook_url") or ""
        old_secret = config.get_param("estate_kit.webhook_secret") or ""

        super().set_values()

        new_url = self.estate_kit_webhook_url or ""
        new_secret = self.estate_kit_webhook_secret or ""

        if new_url == old_url and new_secret == old_secret:
            return

        self._register_webhook(config, new_url, new_secret, old_url)

    def _register_webhook(self, config, new_url, new_secret, old_url):
        client = EstateKitApiClient(self.env)
        if not client._is_configured:
            _logger.warning("Cannot register webhook: API not configured")
            return

        old_subscription_id = config.get_param("estate_kit.webhook_subscription_id") or ""

        if old_subscription_id and old_url != new_url:
            result = client.delete(f"/webhooks/{old_subscription_id}")
            if result is not None:
                _logger.info("Deleted old webhook subscription %s", old_subscription_id)
            config.set_param("estate_kit.webhook_subscription_id", "")

        if not new_url or not new_secret:
            return

        result = client.post("/webhooks", {
            "url": new_url,
            "secret": new_secret,
            "events": WEBHOOK_EVENTS,
        })

        if result and result.get("id"):
            config.set_param("estate_kit.webhook_subscription_id", result["id"])
            _logger.info("Registered webhook subscription %s", result["id"])
        else:
            _logger.warning("Failed to register webhook subscription")
