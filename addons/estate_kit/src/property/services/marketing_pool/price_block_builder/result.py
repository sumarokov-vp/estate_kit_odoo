from dataclasses import dataclass


@dataclass(frozen=True)
class PriceBlock:
    text: str
    score: int
