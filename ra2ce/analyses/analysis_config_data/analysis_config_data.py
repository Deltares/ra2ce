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
    NetworkSection,
    OriginsDestinationsSection,
)


@dataclass
class ProjectSection:
    name: str = ""


@dataclass
class AnalysisSectionIndirect:
    name: str = ""
    analysis: str = ""  # should be enum
    disruption_per_category: str = ""
    duration_event: float = math.nan
    duration_disruption: float = math.nan
    fraction_detour: float = math.nan
    fraction_drivethrough: float = math.nan
    rest_capacity: float = math.nan
    maximum_jam: float = math.nan
    partofday: str = ""
    aggregate_wl: str = ""  # should be enum
    threshold: float = math.nan
    weighing: str = ""  # should be enum
    equity_weight: str = ""
    calculate_route_without_disruption: bool = False
    buffer_meters: float = math.nan
    category_field_name: str = ""
    file_name: Path = None
    save_traffic: bool = False
    save_gpkg: bool = False
    save_csv: bool = False


@dataclass
class AnalysisSectionDirect:
    name: str = ""
    analysis: str = ""  # should be enum
    return_period: float = math.nan
    repair_costs: float = math.nan
    evaluation_period: float = math.nan
    interest_rate: float = math.nan
    climate_factor: float = math.nan
    climate_period: float = math.nan
    damage_curve: str = ""
    event_type: str = ""
    risk_calculation: str = ""
    loss_per_distance: str = ""
    traffic_cols: str = ""
    file_name: Path = None
    save_shp: bool = False
    save_gpkg: bool = False
    save_csv: bool = False


@dataclass
class AnalysisSection(AnalysisSectionIndirect, AnalysisSectionDirect):
    pass


@dataclass
class AnalysisConfigData(ConfigDataProtocol):
    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    project: ProjectSection = field(default_factory=lambda: ProjectSection())
    direct: list[AnalysisSectionDirect] = field(default_factory=list)
    indirect: list[AnalysisSectionIndirect] = field(default_factory=list)
    files: Optional[dict[str, Path]] = field(default_factory=dict)
    origins_destinations: Optional[OriginsDestinationsSection] = field(
        default_factory=lambda: OriginsDestinationsSection()
    )
    network: Optional[NetworkSection] = field(default_factory=lambda: NetworkSection())

    def to_dict(self) -> dict:
        _dict = self.__dict__
        _dict["project"] = self.project.__dict__
        _dict["direct"] = [dv.__dict__ for dv in self.direct]
        _dict["indirect"] = [dv.__dict__ for dv in self.indirect]
        _dict["files"] = [dv.__dict__ for dv in self.files]
        return _dict


class AnalysisConfigDataWithNetwork(AnalysisConfigData):
    pass


class AnalysisConfigDataWithoutNetwork(AnalysisConfigData):
    pass
