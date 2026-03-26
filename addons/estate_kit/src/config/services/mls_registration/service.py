from typing import Any

from .protocols import IDataUpdater, IRegistrator, IStatusChecker


class MlsRegistrationService:
    def __init__(
        self,
        registrator: IRegistrator,
        status_checker: IStatusChecker,
        data_updater: IDataUpdater,
    ) -> None:
        self._registrator = registrator
        self._status_checker = status_checker
        self._data_updater = data_updater

    def register(self, settings: Any) -> dict:
        return self._registrator.register(settings)

    def check_status(self, settings: Any) -> dict:
        return self._status_checker.check(settings)

    def update_data(self, settings: Any) -> dict:
        return self._data_updater.update(settings)
