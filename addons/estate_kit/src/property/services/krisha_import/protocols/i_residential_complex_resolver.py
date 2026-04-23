from typing import Protocol


class IResidentialComplexResolver(Protocol):
    def resolve(
        self,
        krisha_complex_id: int | None,
        name: str | None,
        krisha_url: str | None,
        city_id: int | None,
    ) -> int | None: ...
