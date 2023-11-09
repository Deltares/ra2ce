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


@dataclass
class ProjectSection:
    name: str = ""


@dataclass
class AnalysisSection:
    name: str = ""
    analysis: str = ""  # should be enum
    aggregate_wl: str = ""  # should be enum
    threshold: float = math.nan
    weighing: str = ""  # should be enum
    calculate_route_without_disruption: Optional[bool] = False
    buffer_meters: float = math.nan
    category_field_name: str = ""
    save_gpkg: bool = False
    save_csv: bool = False


@dataclass
class AnalysisConfigData(ConfigDataProtocol):
    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    project: ProjectSection = field(default_factory=lambda: ProjectSection())
    direct: list[AnalysisSection] = field(default_factory=list)
    indirect: list[AnalysisSection] = field(default_factory=list)

    def to_dict(self) -> dict:
        _dict = self.__dict__
        _dict["project"] = self.project.__dict__
        _dict["direct"] = [dv.__dict__ for dv in self.direct]
        _dict["indirect"] = [dv.__dict__ for dv in self.indirect]
        return _dict


class AnalysisConfigDataWithNetwork(AnalysisConfigData):
    pass


class AnalysisConfigDataWithoutNetwork(AnalysisConfigData):
    pass
