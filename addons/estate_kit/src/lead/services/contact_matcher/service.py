from .protocols import IPartnerSearcher


class ContactMatcherService:
    def __init__(self, partner_searcher: IPartnerSearcher) -> None:
        self._partner_searcher = partner_searcher

    def match_leads(self, leads) -> None:
        for lead in leads:
            if lead.partner_id:
                continue
            phone = lead.phone
            partner_id = self._partner_searcher.find_by_phone(phone)
            if partner_id:
                lead.partner_id = partner_id
