from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .address.service import AddressService
    from .api_sync.service import ApiSyncService
    from .district_detector.service import DistrictDetectorService
    from .pool_rotation.service import PoolRotationService
    from .property_validator.service import PropertyValidatorService
    from .scoring.service import ScoringService
    from .state_machine.service import StateMachineService
    from .tier_list.service import TierListService
    from .unified_search.service import UnifiedSearchService

_ENV_KEY = "_estate_property_services"


class ServiceLocator:
    def __init__(self, env) -> None:
        self._env = env
        self._cache: dict = {}

    @classmethod
    def get(cls, env) -> ServiceLocator:
        if not hasattr(env, _ENV_KEY):
            setattr(env, _ENV_KEY, cls(env))
        return getattr(env, _ENV_KEY)

    @property
    def state_machine(self) -> StateMachineService:
        return self._resolve("state_machine")

    @property
    def tier_list(self) -> TierListService:
        return self._resolve("tier_list")

    @property
    def scoring(self) -> ScoringService:
        return self._resolve("scoring")

    @property
    def pool_rotation(self) -> PoolRotationService:
        return self._resolve("pool_rotation")

    @property
    def unified_search(self) -> UnifiedSearchService:
        return self._resolve("unified_search")

    @property
    def address(self) -> AddressService:
        return self._resolve("address")

    @property
    def api_sync(self) -> ApiSyncService:
        return self._resolve("api_sync")

    @property
    def district_detector(self) -> DistrictDetectorService:
        return self._resolve("district_detector")

    @property
    def validator(self) -> PropertyValidatorService:
        return self._resolve("property_validator")

    def _resolve(self, name: str):
        if name not in self._cache:
            self._cache[name] = _FACTORIES[name](self._env)
        return self._cache[name]


def _create_state_machine(env):
    from .state_machine import Factory
    return Factory.create(env)


def _create_tier_list(env):
    from .tier_list import Factory
    return Factory.create(env)


def _create_scoring(env):
    from .scoring import Factory
    return Factory.create(env)


def _create_pool_rotation(env):
    from .pool_rotation import Factory
    return Factory.create(env)


def _create_unified_search(env):
    from .unified_search import Factory
    return Factory.create(env)


def _create_address(env):
    from .address import Factory
    return Factory.create(env)


def _create_api_sync(env):
    from .api_sync import Factory
    return Factory.create(env)


def _create_district_detector(env):
    from .district_detector import Factory
    return Factory.create(env)


def _create_property_validator(env):
    from .property_validator import Factory
    return Factory.create(env)


_FACTORIES: dict = {
    "state_machine": _create_state_machine,
    "tier_list": _create_tier_list,
    "scoring": _create_scoring,
    "pool_rotation": _create_pool_rotation,
    "unified_search": _create_unified_search,
    "address": _create_address,
    "api_sync": _create_api_sync,
    "district_detector": _create_district_detector,
    "property_validator": _create_property_validator,
}
