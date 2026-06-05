from dataclasses import dataclass, field


@dataclass
class PublicCardData:
    type_label: str = ""
    state_badge: dict | None = None
    metrics: list[dict] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    contact: dict = field(default_factory=dict)
