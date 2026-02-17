from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.krisha_parser import KrishaParser
from ..services.property_import_service import PropertyImportService


class KrishaParserPreview(models.TransientModel):
    _name = "krisha.parser.preview"
    _description = "Превью результатов парсинга"

    result_ids = fields.One2many(
        "krisha.parser.result",
        "wizard_id",
        string="Результаты",
    )
    total_found = fields.Integer(
        string="Найдено",
        compute="_compute_stats",
    )
    duplicates_count = fields.Integer(
        string="Дубликатов",
        compute="_compute_stats",
    )
    selected_count = fields.Integer(
        string="Выбрано",
        compute="_compute_stats",
    )

    @api.depends("result_ids", "result_ids.is_duplicate", "result_ids.selected")
    def _compute_stats(self):
        for record in self:
            record.total_found = len(record.result_ids)
            record.duplicates_count = len(record.result_ids.filtered("is_duplicate"))
            record.selected_count = len(record.result_ids.filtered("selected"))

    def action_import_selected(self):
        self.ensure_one()

        selected = self.result_ids.filtered("selected")
        if not selected:
            raise UserError(_("Не выбрано ни одного объекта для импорта"))

        parser = KrishaParser()
        service = PropertyImportService(self.env)
        city_mapping = service.get_city_mapping()
        created_properties = self.env["estate.property"]

        for result in selected:
            details = parser.fetch_property_details(result.krisha_url)
            prop = service.create_from_krisha_result(result, details, city_mapping)
            created_properties |= prop
            service.import_photos(prop, result, details, parser)

        return {
            "type": "ir.actions.act_window",
            "res_model": "estate.property",
            "view_mode": "list,form",
            "domain": [("id", "in", created_properties.ids)],
            "target": "current",
            "name": _("Импортированные объекты"),
        }

    def action_select_all(self):
        self.ensure_one()
        self.result_ids.filtered(lambda r: not r.is_duplicate).write({"selected": True})
        return self._reopen_wizard()

    def action_deselect_all(self):
        self.ensure_one()
        self.result_ids.write({"selected": False})
        return self._reopen_wizard()

    def _reopen_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
