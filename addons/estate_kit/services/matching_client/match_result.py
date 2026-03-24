from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    property_id: int
    score: float
