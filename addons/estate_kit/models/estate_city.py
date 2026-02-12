import logging

from odoo import api, fields, models

from odoo.addons.estate_kit.services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)


class EstateCity(models.Model):
    _name = "estate.city"
    _description = "Город"
    _order = "sequence, name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код", index=True)
    external_id = fields.Integer(string="API ID", index=True, copy=False)
    sequence = fields.Integer(string="Порядок", default=10)
    active = fields.Boolean(string="Активен", default=True)

    district_ids = fields.One2many(
        "estate.district",
        "city_id",
        string="Районы",
    )

    @api.model
    def _cron_sync_from_api(self):
        client = EstateKitApiClient(self.env)
        items = client.get("/references/cities")
        if not items:
            return

        for item in items:
            existing = self.search([("external_id", "=", item["id"])], limit=1)
            vals = {"name": item["name"], "external_id": item["id"]}
            if existing:
                existing.write(vals)
            else:
                self.create(vals)

        _logger.info("Synced %d cities from API", len(items))
