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
    Represents all configurable settings for a losses analysis section in RA2CE.

    This class defines parameters for single link redundancy, accessibility,
    and risk/loss analyses, including weighing, traffic, thresholds, and
    output options.

    Attributes
    ----------
    analysis
        Specifies the type of losses/criticality analysis to perform.

    weighing
        Defines the weighing method for the analysis (e.g., length, travel time).

    production_loss_per_capita_per_hour
        Economic loss per capita per hour, if applicable. Required only for losses analysis type.

    traffic_period
        Traffic period for the analysis (e.g., day, peak). Required only for losses analysis type.

    hours_per_traffic_period
        Number of hours corresponding to the selected traffic period. Required only for losses analysis type.

    trip_purposes
        Trip purposes to include in the analysis. Required only for losses analysis type.

    resilience_curves_file
        Path to a file containing resilience curves for losses analysis. Required only for losses analysis type.

    traffic_intensities_file
        Path to a file containing the traffic intensities information. Required only for losses analysis type.

    values_of_time_file
        Path to a file containing value-of-time data. Required only for losses analysis type.

    threshold
        Threshold value used for redundancy or accessibility analyses
        (e.g., maximum tolerable disruption).

    threshold_destinations
        Threshold specifically for destination accessibility.

    equity_weight
        Field name or identifier to apply equity weighting in the analysis.

    calculate_route_without_disruption
        If True, calculates baseline routes without any disruptions for comparison.

    buffer_meters
        Buffer distance in meters to consider around network elements, e.g., for exposure or accessibility.

    category_field_name
        Field name used to categorize links or nodes in the analysis.

    save_traffic
        If True, saves intermediate traffic results during the analysis.

    event_type : EventTypeEnum
        Specifies the type of event or hazard for risk/loss calculations.

    risk_calculation_mode
        Defines the mode of risk calculation (e.g., expected annual loss, scenario-based).

    risk_calculation_year
        Year used for risk or estimated annual loss calculations.
    """


    analysis: AnalysisLossesEnum = field(
        default_factory=lambda: AnalysisLossesEnum.INVALID
    )
    # general
    weighing: WeighingEnum = field(default_factory=lambda: WeighingEnum.NONE)

    # losses
    production_loss_per_capita_per_hour: Optional[float] = math.nan
    traffic_period: Optional[TrafficPeriodEnum] = field(
        default_factory=lambda: TrafficPeriodEnum.DAY
    )
    hours_per_traffic_period: Optional[int] = 0
    trip_purposes: Optional[list[TripPurposeEnum]] = field(
        default_factory=lambda: [TripPurposeEnum.NONE]
    )
    resilience_curves_file: Optional[Path] = None
    traffic_intensities_file: Optional[Path] = None
    values_of_time_file: Optional[Path] = None
    # the redundancy analysis) and the intensities
    # accessibility analyses
    threshold: Optional[float] = 0.0
    threshold_destinations: Optional[float] = math.nan
    equity_weight: Optional[str] = ""
    calculate_route_without_disruption: Optional[bool] = False
    buffer_meters: Optional[float] = math.nan
    category_field_name: Optional[str] = ""
    save_traffic: Optional[bool] = False

    # risk or estimated annual losses related
    event_type: Optional[EventTypeEnum] = field(default_factory=lambda: EventTypeEnum.NONE)
    risk_calculation_mode: Optional[RiskCalculationModeEnum] = field(
        default_factory=lambda: RiskCalculationModeEnum.NONE
    )
    risk_calculation_year: Optional[int] = 0


@dataclass
class AnalysisSectionDamages(AnalysisSectionBase):
    """
    Configuration for a damages analysis section.

    This dataclass reflects all possible settings for performing
    a damages-related analysis. It defines parameters for how road
    damages, risks, and associated outputs should be calculated
    and represented.

    Attributes
    ----------
    analysis : AnalysisDamagesEnum
        Type of damages analysis to perform. Defaults to ``AnalysisDamagesEnum.INVALID``.
    representative_damage_percentage : float, optional
        Percentage of representative damage to apply in the analysis
        (default is 100).
    event_type : EventTypeEnum
        Choose if the damages must be calculated from an event perspective (``EventTypeEnum.EVENT``) or a risk perspective (``EventTypeEnum.RETURN_PERIOD``).
        Defaults to ``EventTypeEnum.NONE``.
    damage_curve : DamageCurveEnum
        Type of damage curves to be used: Huizinga (``DamageCurveEnum.HZ``), OSD (``DamageCurveEnum.OSD``), or manual (``DamageCurveEnum.MAN``).
        Defaults to ``DamageCurveEnum.INVALID``.
    risk_calculation_mode : RiskCalculationModeEnum, optional
        Mode used for risk calculation (e.g., deterministic, probabilistic).
        Defaults to ``RiskCalculationModeEnum.NONE``.
    risk_calculation_year : int, optional
        Year used for risk calculation scenarios. Required if risk_calculation_mode is set to ``RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR`` Defaults to 0 (unspecified).
    create_table : bool, optional

    file_name : Path or None


    Notes
    -----
    This section is typically part of a larger analysis pipeline and
    defines only the configuration parameters, not the computational logic.
    """

    analysis: AnalysisDamagesEnum = field(
        default_factory=lambda: AnalysisDamagesEnum.INVALID
    )
    # road damage
    representative_damage_percentage: Optional[float] = 100
    event_type: EventTypeEnum = field(default_factory=lambda: EventTypeEnum.NONE)
    damage_curve: DamageCurveEnum = field(
        default_factory=lambda: DamageCurveEnum.INVALID
    )
    risk_calculation_mode: RiskCalculationModeEnum = field(
        default_factory=lambda: RiskCalculationModeEnum.NONE
    )
    risk_calculation_year: Optional[int] = 0
    create_table: Optional[bool] = False
    file_name: Optional[Path] = None


@dataclass
class AnalysisSectionAdaptation(AnalysisSectionBase):
    """
    Reflects all possible settings that an adaptation analysis section might contain.
    """

    analysis: AnalysisEnum = AnalysisEnum.ADAPTATION
    losses_analysis: AnalysisLossesEnum = AnalysisLossesEnum.SINGLE_LINK_LOSSES
    # Economical settings
    time_horizon: float = 0.0
    discount_rate: float = 0.0
    # Hazard settings
    initial_frequency: float = 0.0
    climate_factor: float = 0.0
    hazard_fraction_cost: bool = False
    # First option is the no adaptation option
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
    construction_interval: float = 1000.0
    maintenance_cost: float = 0.0
    maintenance_interval: float = 1000.0


@dataclass
class AnalysisConfigData(ConfigDataProtocol):
    """
    Represents all configuration data for analyses in RA2CE, including defaults from analysis.ini.

    This class consolidates analysis configuration settings and integrates relevant network attributes
    (e.g., network, origins/destinations, hazard names) for convenience.

    Attributes
    ----------
    ANALYSIS_SECTION
        Union type for analysis sections (damages, losses, adaptation).

    root_path
        Root directory path for the project.

    input_path
        Input directory path for the project.

    output_path
        Output directory path where results will be saved.

    static_path
        Path to static project files.

    project
        Section containing project metadata.

    analyses
        List of all analysis to run consecutively.

    origins_destinations
        Section containing origins and destinations data.

    network
        Section containing network configuration data.


    """
    ANALYSIS_SECTION = (
            AnalysisSectionDamages | AnalysisSectionLosses | AnalysisSectionAdaptation
    )
    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    project: ProjectSection = field(default_factory=ProjectSection)
    analyses: list[AnalysisSectionDamages | AnalysisSectionLosses | AnalysisSectionAdaptation] = field(default_factory=list)
    origins_destinations: Optional[OriginsDestinationsSection] = field(
        default_factory=OriginsDestinationsSection
    )
    network: NetworkSection = field(default_factory=NetworkSection)
    aggregate_wl: AggregateWlEnum = field(default_factory=lambda: AggregateWlEnum.NONE)

    def reroot_analysis_config(
        self,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
        new_root: Path,
    ) -> AnalysisConfigData:
        """
        Reroot dependent analysis in config data to the input of another analysis.

        Returns:
            AnalysisConfigData: The rerooted config data.
        """

        def reroot_path(orig_path: Optional[Path]) -> Optional[Path]:
            # Rewrite the path to the new root
            if not orig_path or not self.root_path:
                return None
            _orig_parts = orig_path.parts
            _rel_path = Path(*_orig_parts[len(self.root_path.parts) :])
            return new_root.joinpath(analysis_type.config_value, _rel_path)

        self.input_path = reroot_path(self.input_path)

        # Rewrite the paths of the input files in the analysis config
        _analysis = self.get_analysis(analysis_type)
        if isinstance(_analysis, AnalysisSectionDamages):
            _analysis.file_name = reroot_path(_analysis.file_name)
        elif isinstance(_analysis, AnalysisSectionLosses):
            _analysis.resilience_curves_file = reroot_path(
                _analysis.resilience_curves_file
            )
            _analysis.traffic_intensities_file = reroot_path(
                _analysis.traffic_intensities_file
            )
            _analysis.values_of_time_file = reroot_path(_analysis.values_of_time_file)

        self.root_path = new_root

        return self

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
    ) -> ANALYSIS_SECTION | None:
        """
        Get a certain analysis from config.

        Returns:
            AnalysisSectionLosses | AnalysisSectionDamages | AnalysisSectionAdaptation:
                The analysis.
        """
        return next(filter(lambda x: x.analysis == analysis, self.analyses), None)

    @staticmethod
    def get_data_output(ini_file: Path) -> Path:
        return ini_file.parent.joinpath("output")
