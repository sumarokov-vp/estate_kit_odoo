from .partner_creator import PartnerCreator
from .partner_searcher import PartnerSearcher
from .phone_normalizer import PhoneNormalizer
from .service import ContactMatcherService


class Factory:
    @staticmethod
    def create(env) -> ContactMatcherService:
        normalizer = PhoneNormalizer()
        partner_searcher = PartnerSearcher(env, normalizer)
        partner_creator = PartnerCreator(env)
        return ContactMatcherService(partner_searcher, partner_creator)
