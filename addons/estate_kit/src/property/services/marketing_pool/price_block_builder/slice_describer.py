from .protocols import IPropertyTypeLabelResolver


class SliceDescriber:
    def __init__(self, property_type_label_resolver: IPropertyTypeLabelResolver) -> None:
        self._property_type_label_resolver = property_type_label_resolver

    def describe_slice(
        self,
        city_name: str,
        property_type_actual: str,
        property_type_benchmark: str,
    ) -> str:
        benchmark_label = self._property_type_label_resolver.resolve(property_type_benchmark)
        base = "%s, тип «%s»" % (city_name, benchmark_label)
        if property_type_actual != property_type_benchmark:
            actual_label = self._property_type_label_resolver.resolve(property_type_actual)
            base += " (%s учитывается как %s)" % (actual_label, benchmark_label)
        return base

    def describe_relax(
        self,
        relax_level: str,
        district_name: str | None,
        rooms: int,
    ) -> str:
        if relax_level == "exact":
            district = district_name if district_name else "без района"
            return "%s, %d комнат" % (district, rooms)
        if relax_level == "no_rooms":
            district = district_name if district_name else "без района"
            return "%s, все комнаты" % district
        if relax_level == "city_only":
            return "только город (район/комнаты не учитывались — недостаточно выборки)"
        return relax_level
