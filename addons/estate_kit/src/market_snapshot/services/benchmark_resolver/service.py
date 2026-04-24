from .benchmark import MarketBenchmark
from .config import BenchmarkResolverConfig
from .protocols import IAggregatedResolver, IPropertyTypeNormalizer, ISnapshotLookup


class BenchmarkResolverService:
    def __init__(
        self,
        lookup: ISnapshotLookup,
        aggregated_resolver: IAggregatedResolver,
        property_type_normalizer: IPropertyTypeNormalizer,
        config: BenchmarkResolverConfig,
    ) -> None:
        self._lookup = lookup
        self._aggregated_resolver = aggregated_resolver
        self._property_type_normalizer = property_type_normalizer
        self._config = config

    def resolve(self, prop) -> MarketBenchmark | None:
        if not prop.city_id:
            return None

        city_id = prop.city_id.id
        district_id = prop.district_id.id if prop.district_id else None
        property_type = self._property_type_normalizer.normalize(prop.property_type)
        rooms = prop.rooms if prop.rooms else None
        window = self._config.window_days

        relax_chain: list[tuple[str, int | None, int | None]] = [
            ("exact", district_id, rooms),
            ("no_rooms", district_id, None),
            ("city_only", None, None),
        ]

        for relax_level, relax_district, relax_rooms in relax_chain:
            aggregated = self._aggregated_resolver.resolve(
                city_id=city_id,
                district_id=relax_district,
                property_type=property_type,
                rooms=relax_rooms,
                max_age_days=window,
            )
            if aggregated is not None:
                snapshot = self._lookup.browse_snapshot(aggregated.latest_snapshot_id)
                stats = aggregated.stats
                median = stats.median_price_per_sqm
                p25 = stats.p25_price_per_sqm
                p75 = stats.p75_price_per_sqm
                sample_size = stats.sample_size
            else:
                snapshot = self._lookup.find_latest(
                    city_id=city_id,
                    district_id=relax_district,
                    property_type=property_type,
                    rooms=relax_rooms,
                    max_age_days=window,
                )
                if not snapshot:
                    continue
                median = snapshot.median_price_per_sqm
                p25 = snapshot.p25_price_per_sqm
                p75 = snapshot.p75_price_per_sqm
                sample_size = snapshot.sample_size

            return MarketBenchmark(
                median_price_per_sqm=median,
                p25_price_per_sqm=p25,
                p75_price_per_sqm=p75,
                sample_size=sample_size,
                snapshot_id=snapshot.id,
                collected_at=snapshot.collected_at,
                city_name=snapshot.city_id.name,
                district_name=(
                    snapshot.district_id.name if snapshot.district_id else None
                ),
                property_type=snapshot.property_type,
                rooms=snapshot.rooms if relax_level == "exact" else 0,
                relax_level=relax_level,
            )

        return None
