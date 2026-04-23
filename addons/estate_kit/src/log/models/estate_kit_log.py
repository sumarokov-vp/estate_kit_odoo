import logging
from datetime import datetime

from odoo import SUPERUSER_ID, api, fields, models

_logger = logging.getLogger(__name__)


class EstateKitLog(models.Model):
    _name = "estate.kit.log"
    _description = "Логи Estate Kit"
    _order = "id desc"

    timestamp = fields.Datetime(
        string="Время",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    timestamp_display = fields.Char(
        string="Время (мс)",
    )
    category = fields.Char(
        string="Категория",
        required=True,
        index=True,
    )
    level = fields.Selection(
        [
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        string="Уровень",
        default="info",
        required=True,
    )
    summary = fields.Char(string="Описание", required=True)
    details = fields.Text(string="Подробности")
    property_id = fields.Many2one(
        "estate.property",
        string="Объект",
        ondelete="set null",
        index=True,
    )

    @api.model
    def log(self, category, summary, details=None, level="info", property_id=None):
        now = datetime.now()
        display = now.strftime("%d.%m.%Y %H:%M:%S.") + "%03d" % (now.microsecond // 1000)
        values = {
            "category": category,
            "summary": summary,
            "details": details,
            "level": level,
            "property_id": property_id,
            "timestamp_display": display,
        }
        with self.env.registry.cursor() as cr:
            api.Environment(cr, SUPERUSER_ID, {})["estate.kit.log"].create(values)
