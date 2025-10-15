import math
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_data.losses_analysis_config_data_protocol import (
    LossesAnalysisConfigDataProtocol,
)
from ra2ce.common.validation.validation_report import ValidationReport


@dataclass
class BaseOriginDestinationConfigData(LossesAnalysisConfigDataProtocol, ABC):
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
        if (
            not isinstance(self.weighing, WeighingEnum)
            or self.weighing == WeighingEnum.INVALID
            or self.weighing == WeighingEnum.NONE
        ):
            _report.error(
                f"For origin-destination analysis '{self.name}': 'weighing' must be a valid WeighingEnum value."
            )
        return _report

@dataclass
class OptimalRouteOriginDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for optimal route origin-destination analysis."""

    @property
    def config_name(self) -> str:
        return AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION.config_value

@dataclass
class OptimalRouteOriginClosestDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for optimal route origin-closest destination analysis."""

    @property
    def config_name(self) -> str:
        return AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION.config_value

@dataclass
class MultiLinkOriginDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for multi-link origin-destination analysis."""

    @property
    def config_name(self) -> str:
        return AnalysisLossesEnum.MULTI_LINK_ORIGIN_DESTINATION.config_value

@dataclass
class MultiLinkOriginClosestDestinationConfigData(BaseOriginDestinationConfigData):
    """Configuration data for multi-link origin-closest destination analysis."""

    @property
    def config_name(self) -> str:
        return AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION.config_value
@dataclass
class MultiLinkIsolatedLocationsConfigData(BaseOriginDestinationConfigData):
    """Configuration data for multi-link isolated locations analysis."""

    category_field_name: Optional[str] = None

    @property
    def config_name(self) -> str:
        return AnalysisLossesEnum.MULTI_LINK_ISOLATED_LOCATIONS.config_value
