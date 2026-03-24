from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MatchingClientConfig:
    base_url: str

    @classmethod
    def from_env(cls, env: Any) -> "MatchingClientConfig":
        get_param = env["ir.config_parameter"].sudo().get_param
        return cls(
            base_url=get_param("estate_kit.matching_service_url", "http://localhost:8001"),
        )
