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

from dataclasses import dataclass, field

from ra2ce.analysis.analysis_config_data.adaptation_option_config_data import (
    AdaptationOptionConfigData,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.common.validation.validation_report import ValidationReport


@dataclass
class AdaptationOptionConfigData:
    """
    Reflects all possible settings that an adaptation option might contain.
    The id should be unique and is used to determine the location of the input and output files.
    """

    id: str = ""
    name: str = ""
    construction_cost: float = 0.0
    construction_interval: float = 1000.0
    maintenance_cost: float = 0.0
    maintenance_interval: float = 1000.0    


@dataclass
class AdaptationConfigData(AnalysisConfigDataProtocol):
    """
    Configuration data for adaptation analysis.
    """

    name: str
    save_csv: bool = False  # Save results as CSV
    save_gpkg: bool = False  # Save results as GPKG

    losses_analysis: AnalysisLossesEnum = AnalysisLossesEnum.SINGLE_LINK_LOSSES

    # Economical settings
    time_horizon: float = 0.0
    discount_rate: float = 0.0
    # Hazard settings
    initial_frequency: float = 0.0
    climate_factor: float = 0.0
    hazard_fraction_cost: bool = False
    # First option is the no adaptation option
    adaptation_options: list[AdaptationOptionConfigData] = field(
        default_factory=list
    )

    def validate_integrity(self) -> ValidationReport:
        _report = ValidationReport()

        if not self.name:
            _report.error("An analysis 'name' must be provided.")

        return _report
