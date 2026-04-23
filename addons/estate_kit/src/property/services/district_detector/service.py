from odoo.exceptions import UserError

from ..address.service import AddressService
from .protocols import IGeocoder


class DistrictDetectorService:
    def __init__(self, geocoder: IGeocoder, env) -> None:
        self._geocoder = geocoder
        self._env = env

    def detect(self, record) -> None:
        record.ensure_one()
        if not self._geocoder.is_configured:
            raise UserError("API ключ 2GIS не настроен")

        address_parts = AddressService.build_parts(record, include_district=False)
        if not address_parts:
            raise UserError("Укажите адрес для определения района")

        coords = self._geocoder.geocode_address(", ".join(address_parts))
        if not coords:
            raise UserError(f"Адрес не найден: {', '.join(address_parts)}")

        lat, lon = coords
        if not record.latitude or not record.longitude:
            record.latitude = lat
            record.longitude = lon

        if record.city_id:
            district = self._geocoder.find_or_create_district(
                self._env, lat, lon, record.city_id.id,
            )
            if district:
                record.district_id = district.id
