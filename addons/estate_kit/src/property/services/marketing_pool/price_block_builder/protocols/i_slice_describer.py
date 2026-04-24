from typing import Protocol


class ISliceDescriber(Protocol):
    def describe_slice(
        self,
        city_name: str,
        property_type_actual: str,
        property_type_benchmark: str,
    ) -> str: ...

    def describe_relax(
        self,
        relax_level: str,
        district_name: str | None,
        rooms: int,
    ) -> str: ...
