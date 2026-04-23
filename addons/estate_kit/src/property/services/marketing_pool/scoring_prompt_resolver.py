from .prompts import SCORING_PROMPTS, SCORING_PROMPTS_WITH_BENCHMARK


class ScoringPromptResolver:
    def resolve(self, property_type: str, with_benchmark: bool = False) -> str:
        prompts = SCORING_PROMPTS_WITH_BENCHMARK if with_benchmark else SCORING_PROMPTS
        return prompts.get(property_type, prompts["apartment"])
