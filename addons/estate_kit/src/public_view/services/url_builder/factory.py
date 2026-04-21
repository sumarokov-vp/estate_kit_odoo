from .config_base_url_provider import ConfigBaseUrlProvider
from .service import UrlBuilderService


class Factory:
    @staticmethod
    def create(env) -> UrlBuilderService:
        return UrlBuilderService(ConfigBaseUrlProvider(env))
