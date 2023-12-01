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

from ra2ce.analyses.analysis_config_data.enums.analysis_direct_enum import (
    AnalysisDirectEnum,
)
from ra2ce.analyses.analysis_config_data.enums.analysis_indirect_enum import (
    AnalysisIndirectEnum,
)
from ra2ce.analyses.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from ra2ce.graph.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.graph.network_config_data.network_config_data import (
    NetworkSection,
    OriginsDestinationsSection,
)

IndirectAnalysisNameList: list[str] = list(
    map(str, AnalysisIndirectEnum.list_valid_options())
)
DirectAnalysisNameList: list[str] = list(
    map(str, AnalysisDirectEnum.list_valid_options())
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
    Reflects all common settings that direct and indirect analysis sections might contain.
    """

    name: str = ""
    save_gpkg: bool = False
    save_csv: bool = False


@dataclass
class AnalysisSectionIndirect(AnalysisSectionBase):
    """
    Reflects all possible settings that an indirect analysis section might contain.
    """

    analysis: AnalysisIndirectEnum = field(
        default_factory=lambda: AnalysisIndirectEnum.INVALID
    )
    # general
    weighing: WeighingEnum = field(default_factory=lambda: WeighingEnum.NONE)
    loss_per_distance: str = ""
    loss_type: str = ""  # should be enum
    disruption_per_category: str = ""
    traffic_cols: list[str] = field(default_factory=list)
    # losses
    duration_event: float = math.nan
    duration_disruption: float = math.nan
    fraction_detour: float = math.nan
    fraction_drivethrough: float = math.nan
    rest_capacity: float = math.nan
    maximum_jam: float = math.nan
    partofday: str = ""
    # accessibility analyses
    aggregate_wl: AggregateWlEnum = field(default_factory=lambda: AggregateWlEnum.NONE)
    threshold: float = math.nan
    threshold_destinations: float = math.nan
    uniform_duration: float = math.nan
    gdp_percapita: float = math.nan
    equity_weight: str = ""
    calculate_route_without_disruption: bool = False
    buffer_meters: float = math.nan
    threshold_locations: float = math.nan
    category_field_name: str = ""
    save_traffic: bool = False


@dataclass
class AnalysisSectionDirect(AnalysisSectionBase):
    """
    Reflects all possible settings that a direct analysis section might contain.
    """

    analysis: AnalysisDirectEnum = field(
        default_factory=lambda: AnalysisDirectEnum.INVALID
    )
    # adaptation/effectiveness measures
    return_period: float = math.nan
    repair_costs: float = math.nan
    evaluation_period: float = math.nan
    interest_rate: float = math.nan
    climate_factor: float = math.nan
    climate_period: float = math.nan
    # road damage
    damage_curve: str = ""
    event_type: str = ""  # should be enum
    risk_calculation: str = ""  # should be enum
    create_table: bool = False
    file_name: Optional[Path] = None


@dataclass
class AnalysisConfigData(ConfigDataProtocol):
    """
    Reflects all config data from analysis.ini with defaults set.
    Additionally some attributes from the network config are added for completeness (files, origins_destinations, network, hazard_names)
    """

    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    project: ProjectSection = field(default_factory=lambda: ProjectSection())
    analyses: list[AnalysisSectionBase] = field(default_factory=list)
    origins_destinations: Optional[OriginsDestinationsSection] = field(
        default_factory=lambda: OriginsDestinationsSection()
    )
    network: NetworkSection = field(default_factory=lambda: NetworkSection())
    hazard_names: list[str] = field(default_factory=list)

    @property
    def direct(self) -> list[AnalysisSectionDirect]:
        """
        Get all direct analyses from config.

        Returns:
            list[AnalysisSectionDirect]: List of all direct analyses.
        """
        return list(
            filter(lambda x: isinstance(x, AnalysisSectionDirect), self.analyses)
        )

    @property
    def indirect(self) -> list[AnalysisSectionIndirect]:
        """
        Get all indirect analyses from config.

        Returns:
            list[AnalysisSectionIndirect]: List of all indirect analyses.
        """
        return list(
            filter(lambda x: isinstance(x, AnalysisSectionIndirect), self.analyses)
        )

    @staticmethod
    def get_data_output(ini_file: Path) -> Path:
        return ini_file.parent.joinpath("output")
