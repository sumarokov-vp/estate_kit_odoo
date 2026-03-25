from .partner_searcher import PartnerSearcher
from .phone_normalizer import PhoneNormalizer
from .service import ContactMatcherService


class Factory:
    @staticmethod
    def create(env) -> ContactMatcherService:
        normalizer = PhoneNormalizer()
        partner_searcher = PartnerSearcher(env, normalizer)
        return ContactMatcherService(partner_searcher)
