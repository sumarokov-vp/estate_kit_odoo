from ..contact_matcher import Factory as ContactMatcherFactory
from .service import LeadCreatorService


class Factory:
    @staticmethod
    def create(env) -> LeadCreatorService:
        contact_matcher = ContactMatcherFactory.create(env)
        return LeadCreatorService(contact_matcher)
