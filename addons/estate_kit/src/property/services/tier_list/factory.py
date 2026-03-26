from .service import TierListService
from .tier_limit_checker import TierLimitChecker
from .tier_max_limit_validator import TierMaxLimitValidator
from .tier_role_resolver import TierRoleResolver


class Factory:
    @staticmethod
    def create(env) -> TierListService:
        tier_role_resolver = TierRoleResolver(env)
        limit_checker = TierLimitChecker(env)
        tier_max_limit_validator = TierMaxLimitValidator(limit_checker, env)
        return TierListService(tier_role_resolver, tier_max_limit_validator, env)
