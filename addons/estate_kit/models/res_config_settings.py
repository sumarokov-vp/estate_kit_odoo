import logging

from odoo import api, fields, models

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

    @api.model
    def get_twogis_api_key(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.twogis_api_key", "")
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
        base_url = config.get_param("web.base.url") or ""
        if base_url:
            payload["webhook_url"] = f"{base_url}/estatekit/webhook"

        resp = client.post_public("/tenants/register", payload)
        if resp is None:
            return self._notify("Ошибка соединения с API", "danger")
        if resp.status_code not in (200, 201, 202):
            return self._notify(f"Ошибка API: {resp.status_code} {resp.text[:200]}", "danger")

        data = resp.json()
        if resp.status_code == 200:
            return self._notify("Данные совпадают, изменений нет", "info")

        request_code = data.get("request_code", "")
        status = data.get("status", "pending")

        config.set_param("estate_kit.reg_request_code", request_code)
        config.set_param("estate_kit.reg_status", status)

        return self._reload_settings()

    def action_resend_registration(self):
        config = self.env["ir.config_parameter"].sudo()
        company_name = config.get_param("estate_kit.reg_company_name") or ""
        email = config.get_param("estate_kit.reg_email") or ""
        phone = config.get_param("estate_kit.reg_phone") or ""

        client = EstateKitApiClient(self.env)
        if not client.api_url or not company_name or not email:
            return self._notify("Нет данных для повторной отправки", "danger")

        payload: dict[str, str] = {"company_name": company_name, "email": email}
        if phone:
            payload["phone"] = phone
        base_url = config.get_param("web.base.url") or ""
        if base_url:
            payload["webhook_url"] = f"{base_url}/estatekit/webhook"

        resp = client.post_public("/tenants/register", payload)
        if resp is None:
            return self._notify("Ошибка соединения с API", "danger")
        if resp.status_code not in (200, 201, 202):
            return self._notify(f"Ошибка API: {resp.status_code} {resp.text[:200]}", "danger")

        data = resp.json()
        if resp.status_code == 200:
            return self._notify("Данные совпадают, изменений нет", "info")

        request_code = data.get("request_code", "")
        status = data.get("status", "pending")
        config.set_param("estate_kit.reg_request_code", request_code)
        config.set_param("estate_kit.reg_status", status)

        return self._notify("Заявка отправлена повторно", "success")

    def action_check_registration_status(self):
        config = self.env["ir.config_parameter"].sudo()
        request_code = config.get_param("estate_kit.reg_request_code") or ""
        email = config.get_param("estate_kit.reg_email") or ""
        current_status = config.get_param("estate_kit.reg_status") or ""

        client = EstateKitApiClient(self.env)
        if not client.api_url or not request_code or not email:
            return self._notify("Нет данных для проверки", "danger")

        if current_status == "pending_update":
            endpoint = f"/tenants/update/{request_code}"
        else:
            endpoint = f"/tenants/register/{request_code}"

        resp = client.get_public(endpoint, params={"email": email})
        if resp is None:
            return self._notify("Ошибка соединения с API", "danger")
        if resp.status_code == 404:
            return self._notify("Заявка не найдена в API", "warning")
        if resp.status_code != 200:
            return self._notify(f"Ошибка API: {resp.status_code}", "danger")

        data = resp.json()
        status = data.get("status", "unknown")

        if status == "approved":
            if current_status == "pending_update":
                config.set_param("estate_kit.reg_status", "active")
            else:
                if data.get("api_key"):
                    config.set_param("estate_kit.api_key", data["api_key"])
                if data.get("webhook_secret"):
                    config.set_param("estate_kit.webhook_secret", data["webhook_secret"])
                config.set_param("estate_kit.reg_status", "active")
        else:
            config.set_param("estate_kit.reg_status", status)

        return self._reload_settings()

    def action_update_tenant_data(self):
        self.set_values()
        config = self.env["ir.config_parameter"].sudo()
        email = config.get_param("estate_kit.reg_email") or ""

        client = EstateKitApiClient(self.env)
        if not client.api_url or not email:
            return self._notify("Нет данных для обновления", "danger")

        payload: dict[str, str] = {"email": email}
        company_name = self.estate_kit_reg_company_name
        phone = self.estate_kit_reg_phone
        if company_name:
            payload["company_name"] = company_name
        if phone:
            payload["phone"] = phone
        base_url = config.get_param("web.base.url") or ""
        if base_url:
            payload["webhook_url"] = f"{base_url}/estatekit/webhook"

        resp = client.post_public("/tenants/update", payload)
        if resp is None:
            return self._notify("Ошибка соединения с API", "danger")
        if resp.status_code == 404:
            return self._notify("Активная подписка не найдена", "warning")
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
