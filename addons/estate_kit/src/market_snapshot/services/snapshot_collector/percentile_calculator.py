class PercentileCalculator:
    def calculate(self, sorted_samples: list[float], percentile: int) -> float:
        if not sorted_samples:
            return 0.0
        if len(sorted_samples) == 1:
            return sorted_samples[0]
        position = (len(sorted_samples) - 1) * percentile / 100.0
        lower = int(position)
        upper = min(lower + 1, len(sorted_samples) - 1)
        weight = position - lower
        return sorted_samples[lower] * (1 - weight) + sorted_samples[upper] * weight
