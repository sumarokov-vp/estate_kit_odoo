class OutlierTrimmer:
    def __init__(self, cut_percent: float) -> None:
        self._cut_percent = cut_percent

    def trim(self, samples: list[float]) -> list[float]:
        if self._cut_percent <= 0 or self._cut_percent >= 0.5:
            return list(samples)
        sorted_samples = sorted(samples)
        n = len(sorted_samples)
        drop = int(n * self._cut_percent)
        if drop == 0:
            return sorted_samples
        return sorted_samples[drop : n - drop]
