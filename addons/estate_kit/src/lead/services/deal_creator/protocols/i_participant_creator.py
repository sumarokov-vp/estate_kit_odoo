from typing import Protocol


class IParticipantCreator(Protocol):
    def create_for_deal(self, deal, lead) -> None: ...
