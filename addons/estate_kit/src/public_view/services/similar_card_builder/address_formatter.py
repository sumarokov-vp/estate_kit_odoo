class AddressFormatter:
    def format(self, prop) -> str:
        parts = []
        if prop.city_id:
            parts.append(prop.city_id.name)
        if prop.district_id:
            parts.append(prop.district_id.name)
        if prop.street_id:
            parts.append(prop.street_id.name)
        if prop.house_number:
            parts.append(prop.house_number)
        return ", ".join(p for p in parts if p)
