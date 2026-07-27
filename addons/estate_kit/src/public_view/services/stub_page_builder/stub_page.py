from dataclasses import dataclass


@dataclass(frozen=True)
class StubText:
    kind: str
    title: str
    message: str


@dataclass(frozen=True)
class StubPage:
    kind: str
    title: str
    message: str
    contact: dict
