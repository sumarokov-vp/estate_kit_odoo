from .geocoder import YandexGeocoder
from .service import DistrictDetectorService


class Factory:
    @staticmethod
    def create(env) -> DistrictDetectorService:
        geocoder = YandexGeocoder(env)
        return DistrictDetectorService(geocoder, env)
