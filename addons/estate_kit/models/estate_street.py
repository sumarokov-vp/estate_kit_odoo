import logging

from odoo import api, fields, models

from odoo.addons.estate_kit.services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)


class EstateStreet(models.Model):
    _name = "estate.street"
    _description = "Улица"
    _order = "name"

    name = fields.Char(string="Название", required=True, index=True)
    external_id = fields.Integer(string="API ID", index=True, copy=False)
    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        required=True,
        ondelete="restrict",
        index=True,
    )
    district_id = fields.Many2one(
        "estate.district",
        string="Район",
        ondelete="restrict",
    )
    active = fields.Boolean(string="Активен", default=True)

    @api.model
    def _cron_sync_from_api(self):
        client = EstateKitApiClient(self.env)
        items = client.get("/references/streets")
        if not items:
            return

        city_model = self.env["estate.city"]

        for item in items:
            city = city_model.search([("external_id", "=", item["city_id"])], limit=1)
            if not city:
                _logger.warning(
                    "Skipping street '%s' (API ID %d): city with API ID %d not found",
                    item["name"], item["id"], item["city_id"],
                )
                continue

            existing = self.search([("external_id", "=", item["id"])], limit=1)
            vals = {
                "name": item["name"],
                "external_id": item["id"],
                "city_id": city.id,
            }
            if existing:
                existing.write(vals)
            else:
                self.create(vals)

        _logger.info("Synced %d streets from API", len(items))
