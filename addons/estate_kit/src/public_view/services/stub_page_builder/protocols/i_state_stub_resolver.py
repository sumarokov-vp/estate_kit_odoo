from typing import Protocol

from ..stub_page import StubText


class IStateStubResolver(Protocol):
    def resolve(self, prop) -> StubText | None: ...
