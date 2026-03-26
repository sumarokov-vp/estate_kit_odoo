from .expiration_checker import ExpirationChecker
from .expiring_notifier import ExpiringNotifier
from .no_placement_notifier import NoPlacementNotifier
from .orphan_placement_notifier import OrphanPlacementNotifier
from .pool_tag_finder import PoolTagFinder
from .service import PlacementNotificationsService


class Factory:
    @staticmethod
    def create(env) -> PlacementNotificationsService:
        pool_tag_finder = PoolTagFinder()
        return PlacementNotificationsService(
            env=env,
            expiration_checker=ExpirationChecker(),
            no_placement_notifier=NoPlacementNotifier(pool_tag_finder=pool_tag_finder),
            expiring_notifier=ExpiringNotifier(),
            orphan_placement_notifier=OrphanPlacementNotifier(pool_tag_finder=pool_tag_finder),
        )
