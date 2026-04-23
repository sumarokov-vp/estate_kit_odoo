import json
from typing import Any


class ScoringResponseParser:
    def parse(self, response_text: str) -> dict[str, Any] | None:
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        result = json.loads(text)

        for key in ("price_score", "quality_score", "listing_score"):
            if key in result and result[key] is not None:
                score = int(result[key])
                result[key] = max(1, min(10, score))

        result["rationale"] = str(result.get("rationale", ""))
        return result
