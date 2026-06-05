from .protocols import ISimilarityScorer


class Ranker:
    def __init__(self, similarity_scorer: ISimilarityScorer) -> None:
        self._similarity_scorer = similarity_scorer

    def rank(self, prop, candidates, limit: int):
        if not candidates:
            return candidates
        scored = sorted(
            candidates,
            key=lambda candidate: self._similarity_scorer.score(prop, candidate),
            reverse=True,
        )
        top = scored[:limit]
        return candidates.browse([record.id for record in top])
