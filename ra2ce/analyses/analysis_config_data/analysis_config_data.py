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

from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from ra2ce.graph.network_config_data.network_config_data import (
    NetworkConfigData,
    OriginsDestinationsSection,
)

IndirectAnalysisNameList: list[str] = [
    "single_link_redundancy",
    "multi_link_redundancy",
    "optimal_route_origin_destination",
    "multi_link_origin_destination",
    "optimal_route_origin_closest_destination",
    "multi_link_origin_closest_destination",
    "losses",
    "single_link_losses",
    "multi_link_losses",
    "multi_link_isolated_locations",
]
DirectAnalysisNameList: list[str] = ["direct", "effectiveness_measures"]


@dataclass
class ProjectSection:
    name: str = ""


@dataclass
class AnalysisSectionBase:
    name: str = ""
    analysis: str = ""  # should be enum
    save_gpkg: bool = False
    save_csv: bool = False


@dataclass
class AnalysisSectionIndirect(AnalysisSectionBase):
    # general
    weighing: str = ""  # should be enum
    loss_per_distance: str = ""
    loss_type: str = ""  # should be enum
    disruption_per_category: str = ""
    traffic_cols: str = ""  # should be list?
    # losses
    duration_event: float = math.nan
    duration_disruption: float = math.nan
    fraction_detour: float = math.nan
    fraction_drivethrough: float = math.nan
    rest_capacity: float = math.nan
    maximum_jam: float = math.nan
    partofday: str = ""
    # accessiblity analyses
    aggregate_wl: str = ""  # should be enum
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
    # adaptation/effectiveness measures
    return_period: float = math.nan
    repair_costs: float = math.nan
    evaluation_period: float = math.nan
    interest_rate: float = math.nan
    climate_factor: float = math.nan
    climate_period: float = math.nan
    # road damage
    damage_curve: str = ""
    event_type: str = ""
    risk_calculation: str = ""
    create_table: bool = False
    file_name: Optional[Path] = None


@dataclass
class AnalysisConfigData(ConfigDataProtocol):
    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    project: ProjectSection = field(default_factory=lambda: ProjectSection())
    analyses: list[AnalysisSectionBase] = field(default_factory=list)
    files: Optional[dict[str, Path]] = field(default_factory=dict)
    origins_destinations: Optional[OriginsDestinationsSection] = field(
        default_factory=lambda: OriginsDestinationsSection()
    )
    network: Optional[NetworkConfigData] = field(
        default_factory=lambda: NetworkConfigData()
    )
    hazard_names: Optional[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        _dict = self.__dict__
        _dict["project"] = self.project.__dict__
        _dict["direct"] = [dv.__dict__ for dv in self.direct]
        _dict["indirect"] = [dv.__dict__ for dv in self.indirect]
        _dict["files"] = [dv.__dict__ for dv in self.files]
        return _dict

    @property
    def direct(self):
        return list(
            analysis
            for analysis in self.analyses
            if analysis.analysis in DirectAnalysisNameList
        )

    @property
    def indirect(self):
        return list(
            analysis
            for analysis in self.analyses
            if analysis.analysis in IndirectAnalysisNameList
        )


class AnalysisConfigDataWithNetwork(AnalysisConfigData):
    pass


class AnalysisConfigDataWithoutNetwork(AnalysisConfigData):
    pass
