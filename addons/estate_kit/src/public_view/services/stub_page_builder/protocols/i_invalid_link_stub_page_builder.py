from typing import Protocol

from ..stub_page import StubPage


class IInvalidLinkStubPageBuilder(Protocol):
    def build(self) -> StubPage: ...
