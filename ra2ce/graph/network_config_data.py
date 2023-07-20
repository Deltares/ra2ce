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
import abc
from dataclasses import dataclass, field
from pathlib import Path
from configparser import ConfigParser


@dataclass
class NetworkConfigDataBase(abc.ABC):
    def __post_init__(self):
        _keys_with_none = [k for k, v in self.__dict__.items() if v == "None"]
        for k in _keys_with_none:
            self.__dict__[k] = ""


@dataclass
class ProjectSection(NetworkConfigDataBase):
    name: str = ""


@dataclass
class NetworkSection(NetworkConfigDataBase):
    directed: bool = False
    source: str = ""  # should be enum
    primary_file: str = ""
    diversion_file: str = ""
    file_id: str = ""
    polygon: str = ""
    network_type: str = ""  # Should be enum
    road_types: list[str] = field(default_factory=list)
    save_shp: bool = False


@dataclass
class OriginsDestinationsSection(NetworkConfigDataBase):
    # Must be in the static/network folder, belongs to this analysis
    origins: str = ""  # Should be a path.
    # Must be in the static/network folder, belongs to this analysis
    destinations: str = ""  # Should be a path.
    origins_names: str = ""
    destinations_names: str = ""
    id_name_origin_destination: str = ""
    origin_count: str = ""
    origin_out_fraction: int = (
        1  # fraction of things/people going out of the origin to the destination
    )
    category: str = ""
    region: str = ""  # Should be a Path
    region_var: str = ""


@dataclass
class IsolationSection(NetworkConfigDataBase):
    locations: str = ""  # Should be path.


@dataclass
class HazardSection(NetworkConfigDataBase):
    hazard_map: list[str] = field(default_factory=list)  # Should be a list of paths.
    hazard_id: str = ""
    hazard_field_name: str = ""
    aggregate_wl: str = ""  # Should be enum
    hazard_crs: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.hazard_field_name = self.hazard_field_name.split(",")


@dataclass
class CleanupSection(NetworkConfigDataBase):
    snapping_threshold: bool = False
    pruning_threshold: bool = False
    segmentation_length: bool = False
    merge_lines: bool = False
    cut_at_intersections: bool = False


@dataclass
class NetworkConfigData:
    input_path: Path = None
    output_path: Path = None
    static_path: Path = None
    project: ProjectSection = ProjectSection()
    network: NetworkSection = NetworkSection()
    origins_destinations: OriginsDestinationsSection = OriginsDestinationsSection()
    isolation: IsolationSection = IsolationSection()
    hazard: HazardSection = HazardSection()
    cleanup: CleanupSection = CleanupSection()

    @classmethod
    def from_ini_file(cls, ini_file: Path) -> NetworkConfigData:
        _ini_config = ConfigParser(defaults=None)
        _ini_config.read(ini_file)
        return cls(
            input_path=ini_file.parent.joinpath("input"),
            static_path=ini_file.parent.joinpath("static"),
            project=ProjectSection(**_ini_config["project"]),
            network=NetworkSection(**_ini_config["network"]),
            origins_destinations=OriginsDestinationsSection(
                **_ini_config["origins_destinations"]
            ),
            isolation=IsolationSection(
                **_ini_config["isolation"] if "isolation" in _ini_config else {}
            ),
            hazard=HazardSection(**_ini_config["hazard"]),
            cleanup=CleanupSection(**_ini_config["cleanup"]),
        )
