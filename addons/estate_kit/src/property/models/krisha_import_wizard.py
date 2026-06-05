from odoo import fields, models
from odoo.exceptions import UserError

from ..services.krisha_import.factory import Factory as KrishaImportFactory


class KrishaImportWizard(models.TransientModel):
    _name = "estate.krisha.import.wizard"
    _description = "Импорт объекта с Krisha.kz по ссылке"

    url = fields.Char(string="Ссылка на объявление", required=True)

    def action_import(self):
        self.ensure_one()
        url = (self.url or "").strip()
        if not url or "krisha.kz" not in url:
            raise UserError("Укажите корректную ссылку на объявление Krisha.kz.")

        result = KrishaImportFactory.create(self.env).import_one(url)

        if result.is_duplicate:
            raise UserError("Этот объект уже импортирован.")
        if result.is_error:
            raise UserError(f"Не удалось импортировать объект: {result.error_message}")

        return {
            "type": "ir.actions.act_window",
            "res_model": "estate.property",
            "res_id": result.property_id,
            "view_mode": "form",
            "target": "current",
        }
