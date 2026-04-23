from .config import HedonicCoefficients
from .protocols.i_hedonic_multiplier_calculator import HedonicMultiplierResult


class HedonicMultiplierCalculator:
    def __init__(self, coefficients: HedonicCoefficients) -> None:
        self._coefficients = coefficients

    def calculate(self, prop) -> HedonicMultiplierResult:
        multiplier = 1.0
        factors: list[str] = []

        if prop.floor and prop.floor == 1:
            multiplier *= self._coefficients.first_floor_penalty
            factors.append(
                "первый этаж ×%.2f" % self._coefficients.first_floor_penalty,
            )
        elif (
            prop.floor
            and prop.floors_total
            and prop.floor == prop.floors_total
        ):
            multiplier *= self._coefficients.last_floor_penalty
            factors.append(
                "последний этаж ×%.2f" % self._coefficients.last_floor_penalty,
            )

        if prop.condition:
            condition_mult = self._coefficients.condition_multipliers.get(
                prop.condition,
            )
            if condition_mult is not None:
                multiplier *= condition_mult
                factors.append(
                    "состояние %s ×%.2f" % (prop.condition, condition_mult),
                )

        if prop.year_built and prop.year_built > 0:
            reference = self._coefficients.year_built_reference
            decades = (reference - prop.year_built) / 10.0
            if decades > 0:
                penalty = decades * self._coefficients.year_built_penalty_per_decade
                age_mult = max(0.7, 1.0 - penalty)
                multiplier *= age_mult
                factors.append(
                    "год постройки %d ×%.2f" % (prop.year_built, age_mult),
                )

        if prop.parking and prop.parking in ("underground", "garage"):
            multiplier *= self._coefficients.parking_bonus
            factors.append("паркинг ×%.2f" % self._coefficients.parking_bonus)

        return HedonicMultiplierResult(multiplier=multiplier, factors_applied=factors)
