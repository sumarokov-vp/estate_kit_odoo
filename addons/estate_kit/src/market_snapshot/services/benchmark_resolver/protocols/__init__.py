from .i_aggregated_resolver import AggregatedResult, IAggregatedResolver
from .i_property_type_normalizer import IPropertyTypeNormalizer
from .i_sample_aggregator import AggregatedStats, ISampleAggregator
from .i_snapshot_lookup import ISnapshotLookup
from .i_snapshot_record import ICityRecord, IDistrictRecord, ISnapshotRecord

__all__ = [
    "AggregatedResult",
    "AggregatedStats",
    "ICityRecord",
    "IAggregatedResolver",
    "IDistrictRecord",
    "IPropertyTypeNormalizer",
    "ISampleAggregator",
    "ISnapshotLookup",
    "ISnapshotRecord",
]
