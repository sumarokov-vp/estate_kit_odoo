from odoo import fields, models

from ..services.matching_client import Factory as MatchingClientFactory
from ..services.matching_client import SearchCriteria


class EstateleadMatch(models.Model):
    _name = "estate.lead.match"
    _description = "Lead Match Result"
    _order = "score desc, match_date desc"

    lead_id = fields.Many2one(
        "crm.lead",
        required=True,
        ondelete="cascade",
        index=True,
    )
    property_id = fields.Many2one(
        "estate.property",
        required=True,
        ondelete="restrict",
    )
    score = fields.Float(string="Score")
    match_date = fields.Datetime(default=fields.Datetime.now)
    state = fields.Selection(
        [
            ("new", "New"),
            ("viewed", "Viewed"),
            ("interested", "Interested"),
            ("rejected", "Rejected"),
        ],
        default="new",
    )

    def _cron_update_matching(self):
        leads = self.env["crm.lead"].search(
            [
                ("active", "=", True),
                ("probability", "not in", [100, 0]),
                ("search_property_type", "!=", False),
            ]
        )

        service = MatchingClientFactory.create(self.env)
        now = fields.Datetime.now()

        for lead in leads:
            criteria = self._build_criteria(lead)
            results = service.search(criteria)

            existing = {
                m.property_id.id: m
                for m in self.search([("lead_id", "=", lead.id)])
            }
            result_ids = {r.property_id for r in results}

            to_unlink = [
                m.id for pid, m in existing.items() if pid not in result_ids
            ]
            if to_unlink:
                self.browse(to_unlink).unlink()

            for result in results:
                if result.property_id in existing:
                    existing[result.property_id].write(
                        {"score": result.score, "match_date": now}
                    )
                else:
                    prop = self.env["estate.property"].browse(result.property_id)
                    if prop.exists():
                        self.create(
                            {
                                "lead_id": lead.id,
                                "property_id": result.property_id,
                                "score": result.score,
                            }
                        )

            lead.write({"last_matching_date": now})

    def _build_criteria(self, lead) -> SearchCriteria:
        return SearchCriteria(
            deal_type=lead.search_deal_type or None,
            property_type=lead.search_property_type or None,
            city=lead.search_city_id.name if lead.search_city_id else None,
            districts=[d.name for d in lead.search_district_ids],
            rooms_min=lead.search_rooms_min or None,
            rooms_max=lead.search_rooms_max or None,
            price_min=float(lead.search_price_min) if lead.search_price_min else None,
            price_max=float(lead.search_price_max) if lead.search_price_max else None,
            area_min=lead.search_area_min or None,
            area_max=lead.search_area_max or None,
        )
