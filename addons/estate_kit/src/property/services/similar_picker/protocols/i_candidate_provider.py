from typing import Protocol


class ICandidateProvider(Protocol):
    def find(self, prop): ...
