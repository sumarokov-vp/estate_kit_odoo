from .protocols import ICandidateProvider, IRanker


class SimilarPickerService:
    def __init__(
        self, candidate_provider: ICandidateProvider, ranker: IRanker
    ) -> None:
        self._candidate_provider = candidate_provider
        self._ranker = ranker

    def pick(self, prop, limit: int = 6):
        candidates = self._candidate_provider.find(prop)
        return self._ranker.rank(prop, candidates, limit)
