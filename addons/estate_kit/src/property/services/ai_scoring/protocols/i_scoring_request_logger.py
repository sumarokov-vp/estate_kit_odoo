from typing import Protocol


class IScoringRequestLogger(Protocol):
    def log_request(self, Log, prop, property_data: dict) -> None: ...
