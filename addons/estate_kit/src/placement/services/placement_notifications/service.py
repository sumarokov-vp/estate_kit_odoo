from .protocols import (
    IExpirationChecker,
    IExpiringNotifier,
    INoPlacementNotifier,
    IOrphanPlacementNotifier,
)


class PlacementNotificationsService:
    def __init__(
        self,
        env,
        expiration_checker: IExpirationChecker,
        no_placement_notifier: INoPlacementNotifier,
        expiring_notifier: IExpiringNotifier,
        orphan_placement_notifier: IOrphanPlacementNotifier,
    ):
        self._env = env
        self._expiration_checker = expiration_checker
        self._no_placement_notifier = no_placement_notifier
        self._expiring_notifier = expiring_notifier
        self._orphan_placement_notifier = orphan_placement_notifier

    def expire_placements(self) -> None:
        self._expiration_checker.expire(self._env)

    def check_notifications(self) -> None:
        self._no_placement_notifier.notify(self._env)
        self._expiring_notifier.notify(self._env)
        self._orphan_placement_notifier.notify(self._env)
