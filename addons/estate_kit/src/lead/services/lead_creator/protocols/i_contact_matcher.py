from typing import Protocol


class IContactMatcher(Protocol):
    def match_leads(self, leads) -> None: ...
