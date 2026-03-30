from typing import Any


class CriteriaCollector:
    def collect(self, lead: Any) -> dict:
        criteria = {}

        if lead.search_property_type:
            criteria["property_type"] = lead.search_property_type

        if lead.search_city_id:
            criteria["city"] = lead.search_city_id.name

        if lead.search_district_ids:
            criteria["districts"] = ", ".join(lead.search_district_ids.mapped("name"))

        if lead.search_rooms_min:
            criteria["rooms_min"] = lead.search_rooms_min
        if lead.search_rooms_max:
            criteria["rooms_max"] = lead.search_rooms_max

        if lead.search_area_min:
            criteria["area_min"] = lead.search_area_min
        if lead.search_area_max:
            criteria["area_max"] = lead.search_area_max

        if lead.search_deal_type:
            criteria["deal_type"] = lead.search_deal_type

        return criteria
