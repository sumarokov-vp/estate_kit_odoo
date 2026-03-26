from typing import Protocol


class ITierRoleResolver(Protocol):
    def get_tier_role(self) -> str | None: ...
