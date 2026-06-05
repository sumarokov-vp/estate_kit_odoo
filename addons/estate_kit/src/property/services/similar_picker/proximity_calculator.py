class ProximityCalculator:
    def calculate(
        self, base: float, value: float, tolerance: float, weight: float
    ) -> float:
        if not base or not value:
            return 0.0
        deviation = abs(value - base) / base
        if deviation <= tolerance:
            return weight * (1 - deviation / tolerance)
        return -weight
