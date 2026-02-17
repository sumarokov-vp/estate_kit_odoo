import base64

from .krisha_parser import KrishaParser

MAX_IMPORT_PHOTOS = 10


class PropertyImportService:
    def __init__(self, env):
        self.env = env

    def create_from_krisha_result(self, result, details, city_mapping):
        city_id = city_mapping.get(result.city.lower()) if result.city else False

        property_vals = {
            "name": result.title or f"{result.rooms}-комн. квартира, {result.area} м²",
            "property_type": "apartment",
            "deal_type": "sale",
            "state": "draft",
            "rooms": result.rooms,
            "area_total": result.area,
            "floor": result.floor,
            "floors_total": result.floors_total,
            "price": result.price,
            "krisha_url": result.krisha_url,
            "latitude": result.latitude,
            "longitude": result.longitude,
            "description": details.get("description", ""),
        }

        if city_id:
            property_vals["city_id"] = city_id

        return self.env["estate.property"].create(property_vals)

    def import_photos(self, prop, result, details, parser):
        photo_urls = result.photo_urls_csv.split(",") if result.photo_urls_csv else []
        if details.get("photo_urls"):
            photo_urls = details["photo_urls"]

        for i, photo_url in enumerate(photo_urls[:MAX_IMPORT_PHOTOS]):
            if not photo_url:
                continue
            image_data = parser.download_image(photo_url)
            if image_data:
                self.env["estate.property.image"].create({
                    "property_id": prop.id,
                    "name": f"Фото {i + 1}",
                    "image": base64.b64encode(image_data).decode("utf-8"),
                    "sequence": i * 10,
                    "is_main": i == 0,
                })

    def get_city_mapping(self):
        cities = self.env["estate.city"].search([])
        mapping = {}
        for city in cities:
            mapping[city.name.lower()] = city.id
            if city.code:
                mapping[city.code.lower()] = city.id
        return mapping
