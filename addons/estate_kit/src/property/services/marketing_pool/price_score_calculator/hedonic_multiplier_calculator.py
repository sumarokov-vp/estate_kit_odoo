from .config import HedonicCoefficients
from .hedonic_factor import HedonicFactor
from .labels import CONDITION_LABELS, PARKING_LABELS
from .protocols.i_hedonic_multiplier_calculator import HedonicMultiplierResult


class HedonicMultiplierCalculator:
    def __init__(self, coefficients: HedonicCoefficients) -> None:
        self._coefficients = coefficients

    def calculate(self, prop) -> HedonicMultiplierResult:
        multiplier = 1.0
        factors: list[HedonicFactor] = []

        if prop.floor and prop.floor == 1:
            multiplier *= self._coefficients.first_floor_penalty
            factors.append(HedonicFactor(
                reason="Первый этаж",
                multiplier=self._coefficients.first_floor_penalty,
            ))
        elif (
            prop.floor
            and prop.floors_total
            and prop.floor == prop.floors_total
        ):
            multiplier *= self._coefficients.last_floor_penalty
            factors.append(HedonicFactor(
                reason="Последний этаж",
                multiplier=self._coefficients.last_floor_penalty,
            ))

        if prop.condition:
            condition_mult = self._coefficients.condition_multipliers.get(
                prop.condition,
            )
            if condition_mult is not None:
                multiplier *= condition_mult
                label = CONDITION_LABELS.get(prop.condition, prop.condition)
                factors.append(HedonicFactor(
                    reason="Состояние «%s»" % label,
                    multiplier=condition_mult,
                ))

        if prop.year_built and prop.year_built > 0:
            reference = self._coefficients.year_built_reference
            decades = (reference - prop.year_built) / 10.0
            if decades > 0:
                penalty = decades * self._coefficients.year_built_penalty_per_decade
                age_mult = max(0.7, 1.0 - penalty)
                multiplier *= age_mult
                factors.append(HedonicFactor(
                    reason="Год постройки %d" % prop.year_built,
                    multiplier=age_mult,
                ))

        if prop.parking and prop.parking in ("underground", "garage"):
            multiplier *= self._coefficients.parking_bonus
            label = PARKING_LABELS.get(prop.parking, prop.parking)
            factors.append(HedonicFactor(
                reason="Паркинг %s" % label,
                multiplier=self._coefficients.parking_bonus,
            ))

        return HedonicMultiplierResult(multiplier=multiplier, factors_applied=factors)
