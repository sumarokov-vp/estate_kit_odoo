from .geocoder import TwoGisGeocoder
from .service import DistrictDetectorService


class Factory:
    @staticmethod
    def create(env) -> DistrictDetectorService:
        geocoder = TwoGisGeocoder(env)
        return DistrictDetectorService(geocoder, env)
