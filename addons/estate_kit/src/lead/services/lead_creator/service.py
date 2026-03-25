from .protocols import IContactMatcher


class LeadCreatorService:
    def __init__(self, contact_matcher: IContactMatcher) -> None:
        self._contact_matcher = contact_matcher

    def after_create(self, records) -> None:
        """Пост-обработка созданных лидов."""
        self._contact_matcher.match_leads(records)
