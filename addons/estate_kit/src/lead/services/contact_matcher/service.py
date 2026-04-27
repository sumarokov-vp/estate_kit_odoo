from .protocols import IPartnerCreator, IPartnerSearcher


class ContactMatcherService:
    def __init__(
        self,
        partner_searcher: IPartnerSearcher,
        partner_creator: IPartnerCreator,
    ) -> None:
        self._partner_searcher = partner_searcher
        self._partner_creator = partner_creator

    def match_leads(self, leads) -> None:
        for lead in leads:
            if lead.partner_id:
                continue
            phone = lead.phone
            if not phone:
                continue
            partner_id = self._partner_searcher.find_by_phone(phone)
            if not partner_id and lead.contact_name:
                partner_id = self._partner_creator.create(lead.contact_name, phone)
            if partner_id:
                lead.partner_id = partner_id
