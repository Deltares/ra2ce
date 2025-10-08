import math
from abc import ABC
from dataclasses import dataclass, field
from typing import Optional

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.configuration.legacy_mappers import with_legacy_mappers


@with_legacy_mappers
@dataclass
class BaseOriginDestinationConfigData(AnalysisConfigDataProtocol, ABC):
    """Base class for origin-destination configuration data."""

    name: str
    save_gpkg: bool = False
    save_csv: bool = False

    # Concrete properties
    weighing: WeighingEnum = field(default_factory=lambda: WeighingEnum.NONE)
    calculate_route_without_disruption: Optional[bool] = False
    threshold: Optional[float] = 0.0
    threshold_destinations: Optional[float] = math.nan
    buffer_meters: Optional[float] = math.nan


class OptimalRouteOriginDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for optimal route origin-destination analysis."""

    pass


class OptimalRouteOriginClosestDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for optimal route origin-closest destination analysis."""

    pass


class MultiLinkOriginDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for multi-link origin-destination analysis."""

    pass


class MultiLinkOriginClosestDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for multi-link origin-closest destination analysis."""

    pass
