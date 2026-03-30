from .mls_rate_provider import MlsRateProvider
from .service import CommissionService
from .settings_rate_provider import SettingsRateProvider


class Factory:
    @staticmethod
    def create(env) -> CommissionService:
        rate_provider = SettingsRateProvider(env)
        mls_rate_provider = MlsRateProvider()
        return CommissionService(rate_provider, mls_rate_provider)
