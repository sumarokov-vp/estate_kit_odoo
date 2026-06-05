from .candidate_provider import CandidateProvider
from .config import DEFAULT_CONFIG
from .proximity_calculator import ProximityCalculator
from .ranker import Ranker
from .service import SimilarPickerService
from .similarity_scorer import SimilarityScorer


class Factory:
    @staticmethod
    def create(env) -> SimilarPickerService:
        scorer = SimilarityScorer(DEFAULT_CONFIG, ProximityCalculator())
        return SimilarPickerService(
            candidate_provider=CandidateProvider(env),
            ranker=Ranker(scorer),
        )
