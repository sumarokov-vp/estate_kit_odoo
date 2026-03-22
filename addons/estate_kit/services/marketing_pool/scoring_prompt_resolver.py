from .prompts import SCORING_PROMPTS


class ScoringPromptResolver:
    def resolve(self, property_type: str) -> str:
        return SCORING_PROMPTS.get(property_type, SCORING_PROMPTS["apartment"])
