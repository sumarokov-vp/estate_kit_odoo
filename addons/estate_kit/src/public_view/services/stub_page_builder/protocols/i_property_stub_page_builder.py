from typing import Protocol

from ..stub_page import StubPage


class IPropertyStubPageBuilder(Protocol):
    def build(self, prop) -> StubPage | None: ...
