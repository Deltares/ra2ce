import math
from abc import ABC
from dataclasses import dataclass, field
from typing import Optional

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.common.validation.validation_report import ValidationReport


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

    def validate_integrity(self) -> ValidationReport:
        _report = ValidationReport()
        if not self.name:
            _report.error("An analysis 'name' must be provided.")
        if not isinstance(self.weighing, WeighingEnum) or self.weighing == WeighingEnum.INVALID or self.weighing == WeighingEnum.NONE:
            _report.error(
                f"For origin-destination analysis '{self.name}': 'weighing' must be a valid WeighingEnum value."
            )
        return _report


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
