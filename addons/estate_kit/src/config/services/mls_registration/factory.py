from ....shared.services.api_client import EstateKitApiClient
from .data_updater import DataUpdater
from .registrator import MlsRegistrator
from .service import MlsRegistrationService
from .status_checker import StatusChecker


class Factory:
    @staticmethod
    def create(env) -> MlsRegistrationService:
        api_client = EstateKitApiClient(env)
        config_params = env["ir.config_parameter"].sudo()
        registrator = MlsRegistrator(api_client, config_params)
        status_checker = StatusChecker(api_client, config_params)
        data_updater = DataUpdater(api_client, config_params)
        return MlsRegistrationService(registrator, status_checker, data_updater)
