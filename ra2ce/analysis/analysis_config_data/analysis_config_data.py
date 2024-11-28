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

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.loss_type_enum import LossTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.network_config_data import (
    NetworkSection,
    OriginsDestinationsSection,
)

LossesAnalysisNameList: list[str] = list(
    map(str, AnalysisLossesEnum.list_valid_options())
)
DamagesAnalysisNameList: list[str] = list(
    map(str, AnalysisDamagesEnum.list_valid_options())
)


@dataclass
class ProjectSection:
    """
    Reflects all possible settings that a project section might contain.
    """

    name: str = ""


@dataclass
class AnalysisSectionBase:
    """
    Reflects all common settings that damages and losses analysis sections might contain.
    """

    name: str = ""
    save_gpkg: bool = False
    save_csv: bool = False


@dataclass
class AnalysisSectionLosses(AnalysisSectionBase):
    """
    Reflects all possible settings that a losses analysis section might contain.
    """

    analysis: AnalysisLossesEnum = field(
        default_factory=lambda: AnalysisLossesEnum.INVALID
    )
    # general
    weighing: WeighingEnum = field(default_factory=lambda: WeighingEnum.NONE)
    loss_per_distance: str = ""
    loss_type: LossTypeEnum = field(default_factory=lambda: LossTypeEnum.NONE)
    disruption_per_category: str = ""
    # losses
    traffic_cols: list[str] = field(default_factory=list)
    production_loss_per_capita_per_hour: float = math.nan
    traffic_period: TrafficPeriodEnum = field(
        default_factory=lambda: TrafficPeriodEnum.DAY
    )
    hours_per_traffic_period: int = 0
    performance: str = "diff_time"  # "diff_time" or "diff_length" relates to the used criticality metric
    trip_purposes: list[TripPurposeEnum] = field(
        default_factory=lambda: [TripPurposeEnum.NONE]
    )
    resilience_curves_file: Optional[Path] = None
    traffic_intensities_file: Optional[Path] = None
    values_of_time_file: Optional[Path] = None
    # the redundancy analysis) and the intensities
    # accessibility analyses
    threshold: float = 0.0
    threshold_destinations: float = math.nan
    uniform_duration: float = math.nan
    gdp_percapita: float = math.nan
    equity_weight: str = ""
    calculate_route_without_disruption: bool = False
    buffer_meters: float = math.nan
    threshold_locations: float = math.nan
    category_field_name: str = ""
    save_traffic: bool = False

    # risk or estimated annual losses related
    event_type: EventTypeEnum = field(default_factory=lambda: EventTypeEnum.NONE)
    risk_calculation_mode: RiskCalculationModeEnum = field(
        default_factory=lambda: RiskCalculationModeEnum.NONE
    )
    risk_calculation_year: int = 0


@dataclass
class AnalysisSectionDamages(AnalysisSectionBase):
    """
    Reflects all possible settings that a damages analysis section might contain.
    """

    analysis: AnalysisDamagesEnum = field(
        default_factory=lambda: AnalysisDamagesEnum.INVALID
    )
    # adaptation/effectiveness measures
    return_period: float = math.nan
    repair_costs: float = math.nan
    evaluation_period: float = math.nan
    interest_rate: float = math.nan
    climate_factor: float = math.nan
    climate_period: float = math.nan
    # road damage
    representative_damage_percentage: float = 100
    event_type: EventTypeEnum = field(default_factory=lambda: EventTypeEnum.NONE)
    damage_curve: DamageCurveEnum = field(
        default_factory=lambda: DamageCurveEnum.INVALID
    )
    risk_calculation_mode: RiskCalculationModeEnum = field(
        default_factory=lambda: RiskCalculationModeEnum.NONE
    )
    risk_calculation_year: int = 0
    create_table: bool = False
    file_name: Optional[Path] = None


@dataclass
class AnalysisSectionAdaptation(AnalysisSectionBase):
    """
    Reflects all possible settings that an adaptation analysis section might contain.
    """

    analysis: AnalysisEnum = AnalysisEnum.ADAPTATION
    discount_rate: float = 0.0
    time_horizon: float = 0.0
    vat: float = 0.0
    climate_factor: float = 0.0
    initial_frequency: float = 0.0
    adaptation_options: list[AnalysisSectionAdaptationOption] = field(
        default_factory=list
    )


@dataclass
class AnalysisSectionAdaptationOption:
    """
    Reflects all possible settings that an adaptation option might contain.
    The id should be unique and is used to determine the location of the input and output files.
    """

    id: str = ""
    name: str = ""
    construction_cost: float = 0.0
    maintenance_interval: float = math.inf
    maintenance_cost: float = 0.0


@dataclass
class AnalysisConfigData(ConfigDataProtocol):
    """
    Reflects all config data from analysis.ini with defaults set.
    Additionally, some attributes from the network config are added for completeness (files, origins_destinations, network, hazard_names)
    """

    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    project: ProjectSection = field(default_factory=ProjectSection)
    analyses: list[AnalysisSectionBase] = field(default_factory=list)
    origins_destinations: Optional[OriginsDestinationsSection] = field(
        default_factory=OriginsDestinationsSection
    )
    network: NetworkSection = field(default_factory=NetworkSection)
    aggregate_wl: AggregateWlEnum = field(default_factory=lambda: AggregateWlEnum.NONE)
    hazard_names: list[str] = field(default_factory=list)

    @property
    def damages_list(self) -> list[AnalysisSectionDamages]:
        """
        Get all damages analyses from config.

        Returns:
            list[AnalysisSectionDamages]: List of all damages analyses.
        """
        return list(
            filter(lambda x: isinstance(x, AnalysisSectionDamages), self.analyses)
        )

    @property
    def losses_list(self) -> list[AnalysisSectionLosses]:
        """
        Get all losses analyses from config.

        Returns:
            list[AnalysisSectionLosses]: List of all losses analyses.
        """
        return list(
            filter(lambda x: isinstance(x, AnalysisSectionLosses), self.analyses)
        )

    @property
    def adaptation(self) -> AnalysisSectionAdaptation | None:
        """
        Get the adaptation analysis from config.

        Returns:
            AnalysisSectionAdaptation: Adaptation analysis.
        """
        return next(
            filter(lambda x: isinstance(x, AnalysisSectionAdaptation), self.analyses),
            None,
        )

    def get_analysis(
        self, analysis: AnalysisEnum | AnalysisDamagesEnum | AnalysisLossesEnum
    ) -> AnalysisSectionBase | None:
        """
        Get a certain analysis from config.

        Returns:
            AnalysisSectionBase: The analysis.
        """
        return next(filter(lambda x: x.analysis == analysis, self.analyses), None)

    @staticmethod
    def get_data_output(ini_file: Path) -> Path:
        return ini_file.parent.joinpath("output")
