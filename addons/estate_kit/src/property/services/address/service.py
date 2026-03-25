class AddressService:
    def __init__(self, env) -> None:
        self._env = env

    def compute_geo_address(self, records) -> None:
        for record in records:
            parts = self.build_parts(record, include_district=True)
            record.geo_address = ", ".join(parts) if parts else False

    def default_city(self):
        code = (
            self._env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.default_city_code", "almaty")
        )
        return self._env["estate.city"].search([("code", "=", code)], limit=1)

    def onchange_city(self, record) -> None:
        if record.district_id and record.district_id.city_id != record.city_id:
            record.district_id = False
        if record.street_id and record.street_id.city_id != record.city_id:
            record.street_id = False

    @staticmethod
    def build_parts(record, include_district: bool = True) -> list[str]:
        parts: list[str] = []
        if record.city_id:
            parts.append(str(record.city_id.name))
        if include_district and record.district_id:
            parts.append(str(record.district_id.name))
        if record.street_id:
            parts.append(str(record.street_id.name))
        if record.house_number:
            parts.append(str(record.house_number))
        return parts
