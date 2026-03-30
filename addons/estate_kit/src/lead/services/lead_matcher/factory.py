from typing import Any

from ..matching_client import Factory as MatchingClientFactory

from .match_repository import MatchRepository
from .service import LeadMatcherService


class Factory:
    @staticmethod
    def create(env: Any) -> LeadMatcherService:
        matching_client = MatchingClientFactory.create(env)
        match_repository = MatchRepository(env)
        return LeadMatcherService(matching_client, match_repository)
