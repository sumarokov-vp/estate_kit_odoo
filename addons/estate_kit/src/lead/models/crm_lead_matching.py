import logging

from requests.exceptions import RequestException

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..services.lead_matcher import Factory as LeadMatcherFactory
from ..services.matching_client import SearchCriteria

_logger = logging.getLogger(__name__)

STAGE_MATCHED_XMLID = "estate_kit.crm_stage_matched"
MIN_MATCHES_FOR_ADVANCE = 1


class CrmLeadMatching(models.Model):
    _inherit = "crm.lead"

    last_matching_date = fields.Datetime(
        string="Последний подбор",
        readonly=True,
        copy=False,
    )
    match_ids = fields.One2many(
        "estate.lead.match",
        "lead_id",
        string="Подобранные объекты",
    )
    match_count = fields.Integer(
        string="Подборки",
        compute="_compute_match_count",
    )

    def _compute_match_count(self):
        for rec in self:
            rec.match_count = len(rec.match_ids)

    def action_match_properties(self):
        self.ensure_one()
        criteria = self._build_match_criteria()
        service = LeadMatcherFactory.create(self.env)
        try:
            count = service.match(self.id, criteria)
        except RequestException as exc:
            _logger.warning("Matching service error for lead %s: %s", self.id, exc)
            raise UserError(_("Сервис подбора недоступен. Попробуйте позже."))

        if count > MIN_MATCHES_FOR_ADVANCE:
            stage = self.env.ref(STAGE_MATCHED_XMLID)
            self.write({"stage_id": stage.id})

    def _build_match_criteria(self) -> SearchCriteria:
        self.ensure_one()
        return SearchCriteria(
            deal_type=self.search_deal_type or None,
            property_type=self.search_property_type or None,
            city=self.search_city_id.name if self.search_city_id else None,
            districts=[d.name for d in self.search_district_ids],
            rooms_min=self.search_rooms_min or None,
            rooms_max=self.search_rooms_max or None,
            price_min=float(self.search_price_min) if self.search_price_min else None,
            price_max=float(self.search_price_max) if self.search_price_max else None,
            area_min=self.search_area_min or None,
            area_max=self.search_area_max or None,
        )
