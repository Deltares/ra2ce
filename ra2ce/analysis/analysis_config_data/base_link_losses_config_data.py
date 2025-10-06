"""
                GNU GENERAL PUBLIC LICENSE
                  Version 3, 29 June 2007

Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
Copyright (C) 2023 Stichting Deltares

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import math
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.common.validation.validation_report import ValidationReport


@dataclass
class BaseLinkLossesConfigData(AnalysisConfigDataProtocol, ABC):
    """
    Reflects all possible settings that a base link losses config might contain.
    """
    # Common properties
    name: str
    save_gpkg: bool = False
    save_csv: bool = False

    # Concrete properties
    event_type: EventTypeEnum = field(default_factory=lambda: EventTypeEnum.NONE)
    weighing: WeighingEnum = field(default_factory=lambda: WeighingEnum.NONE)

    production_loss_per_capita_per_hour: Optional[float] = math.nan
    traffic_period: Optional[TrafficPeriodEnum] = field(
        default_factory=lambda: TrafficPeriodEnum.DAY
    )
    trip_purposes: Optional[list[TripPurposeEnum]] = field(
        default_factory=lambda: [TripPurposeEnum.NONE]
    )
    resilience_curves_file: Optional[Path] = None
    traffic_intensities_file: Optional[Path] = None
    values_of_time_file: Optional[Path] = None

    # Optional properties
    risk_calculation_mode: RiskCalculationModeEnum = field(
        default_factory=lambda: RiskCalculationModeEnum.NONE
    )
    # Risk calculation year is required if 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'
    risk_calculation_year: Optional[int] = None

    def validate_integrity(self) -> ValidationReport:
        _report = ValidationReport()
        if self.risk_calculation_mode == RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR:
            if self.risk_calculation_year is None or self.risk_calculation_year <= 0:
                _report.error(
                    f"For damage analysis '{self.name}': 'risk_calculation_year' should be a positive integer when 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'."
                )
        return _report
    
class MultiLinkLossesConfigData(BaseLinkLossesConfigData):
    """
    Configuration data for multi-link losses analysis.
    """
    pass

class SingleLinkLossesConfigData(BaseLinkLossesConfigData):
    """
    Configuration data for single-link losses analysis.
    """
    pass