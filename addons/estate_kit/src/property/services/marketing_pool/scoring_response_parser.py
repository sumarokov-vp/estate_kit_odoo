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

        if "quality_text" in result:
            result["quality_text"] = str(result.get("quality_text", ""))
        if "listing_text" in result:
            result["listing_text"] = str(result.get("listing_text", ""))
        if "rationale" in result:
            result["rationale"] = str(result.get("rationale", ""))
        return result
