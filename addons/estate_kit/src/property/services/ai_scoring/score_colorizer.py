class ScoreColorizer:
    def colorize(self, score: int) -> str:
        if score <= 3:
            return f"🔴 {score}/10"
        if score <= 6:
            return f"🟡 {score}/10"
        return f"🟢 {score}/10"
