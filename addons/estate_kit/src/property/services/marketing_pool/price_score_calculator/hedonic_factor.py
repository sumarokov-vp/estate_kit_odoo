from dataclasses import dataclass


@dataclass(frozen=True)
class HedonicFactor:
    reason: str
    multiplier: float
