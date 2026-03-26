from dataclasses import dataclass


@dataclass
class MpsResult:
    score: float
    indicator: str
    display: str
