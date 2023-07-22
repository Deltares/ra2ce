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
from dataclasses import dataclass, field
from pathlib import Path
from configparser import ConfigParser
from typing import Union


@dataclass
class ProjectSection:
    name: str = ""


@dataclass
class NetworkSection:
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
class OriginsDestinationsSection:
    # Must be in the static/network folder, belongs to this analysis
    origins: Path = None
    # Must be in the static/network folder, belongs to this analysis
    destinations: Path = None
    origins_names: str = ""
    destinations_names: str = ""
    id_name_origin_destination: str = ""
    origin_count: str = ""
    origin_out_fraction: int = (
        1  # fraction of things/people going out of the origin to the destination
    )
    category: str = ""
    region: Path = None
    region_var: str = ""


@dataclass
class IsolationSection:
    locations: str = ""  # Should be path.


@dataclass
class HazardSection:
    hazard_map: list[Path] = field(default_factory=list)  # Should be a list of paths.
    hazard_id: str = ""
    hazard_field_name: list[str] = field(default_factory=list)
    aggregate_wl: str = ""  # Should be enum
    hazard_crs: str = ""


@dataclass
class CleanupSection:
    snapping_threshold: bool = False
    pruning_threshold: bool = False
    segmentation_length: float = float("nan")
    merge_lines: bool = False
    cut_at_intersections: bool = False


class NetworkConfigDataSectionReader:
    parser: ConfigParser

    def __init__(self, file_to_parse: Path) -> None:
        self.parser = ConfigParser(
            inline_comment_prefixes="#",
            converters={"list": lambda x: [x.strip() for x in x.split(",")]},
        )
        self.parser.read(file_to_parse)
        self._remove_none_values()

    def _get_str_as_path(self, str_value: Union[str, Path]) -> Path:
        if str_value and not isinstance(str_value, Path):
            return Path(str_value)
        return str_value

    def _remove_none_values(self) -> None:
        # Remove 'None' from values, replace them with empty strings
        for _section in self.parser.sections():
            _keys_with_none = [
                k for k, v in self.parser[_section].items() if v == "None"
            ]
            for _key_with_none in _keys_with_none:
                self.parser[_section].pop(_key_with_none)

    def get_sections(self) -> dict:
        return {
            "project": self.get_project_section(),
            "network": self.get_network_section(),
            "origins_destinations": self.get_origins_destinations_section(),
            "isolation": self.get_isolation_section(),
            "hazard": self.get_hazard_section(),
            "cleanup": self.get_cleanup_section(),
        }

    def get_project_section(self) -> ProjectSection:
        return ProjectSection(**self.parser["project"])

    def get_network_section(self) -> NetworkSection:
        _section = "network"
        _network_section = NetworkSection(**self.parser[_section])
        _network_section.directed = self.parser.getboolean(
            _section, "directed", fallback=_network_section.directed
        )
        _network_section.save_shp = self.parser.getboolean(
            _section, "save_shp", fallback=_network_section.save_shp
        )
        _network_section.road_types = self.parser.getlist(
            _section, "road_types", fallback=_network_section.road_types
        )
        return _network_section

    def get_origins_destinations_section(self) -> OriginsDestinationsSection:
        _section = "origins_destinations"
        _od_section = OriginsDestinationsSection(**self.parser[_section])
        _od_section.origin_out_fraction = self.parser.getint(
            _section, "origin_out_fraction", fallback=_od_section.origin_out_fraction
        )
        _od_section.origins = self._get_str_as_path(_od_section.origins)
        _od_section.destinations = self._get_str_as_path(_od_section.destinations)
        _od_section.region = self._get_str_as_path(_od_section.region)
        return _od_section

    def get_isolation_section(self) -> IsolationSection:
        _section = "isolation"
        if _section not in self.parser:
            return IsolationSection()
        return IsolationSection(**self.parser[_section])

    def get_hazard_section(self) -> HazardSection:
        _section = "hazard"
        if _section not in self.parser:
            return HazardSection()
        _hazard_section = HazardSection(**self.parser[_section])
        _hazard_section.hazard_map = list(
            map(
                self._get_str_as_path,
                self.parser.getlist(
                    _section, "hazard_map", fallback=_hazard_section.hazard_map
                ),
            )
        )
        _hazard_section.hazard_field_name = self.parser.getlist(
            _section, "hazard_field_name", fallback=_hazard_section.hazard_field_name
        )
        return _hazard_section

    def get_cleanup_section(self) -> CleanupSection:
        _section = "cleanup"

        _cleanup_section = CleanupSection()
        _cleanup_section.snapping_threshold = self.parser.getboolean(
            _section,
            "snapping_threshold",
            fallback=_cleanup_section.snapping_threshold,
        )
        _cleanup_section.pruning_threshold = self.parser.getboolean(
            _section,
            "pruning_threshold",
            fallback=_cleanup_section.pruning_threshold,
        )
        _cleanup_section.segmentation_length = self.parser.getfloat(
            _section,
            "segmentation_length",
            fallback=_cleanup_section.segmentation_length,
        )
        _cleanup_section.merge_lines = self.parser.getboolean(
            _section, "merge_lines", fallback=_cleanup_section.merge_lines
        )
        _cleanup_section.cut_at_intersections = self.parser.getboolean(
            _section,
            "cut_at_intersections",
            fallback=_cleanup_section.cut_at_intersections,
        )
        return _cleanup_section


@dataclass
class NetworkConfigData:
    input_path: Path = None
    output_path: Path = None
    static_path: Path = None

    project: ProjectSection = field(default_factory=lambda: ProjectSection())
    network: NetworkSection = field(default_factory=lambda: NetworkSection())
    origins_destinations: OriginsDestinationsSection = field(
        default_factory=lambda: OriginsDestinationsSection()
    )
    isolation: IsolationSection = field(default_factory=lambda: IsolationSection())
    hazard: HazardSection = field(default_factory=lambda: HazardSection())
    cleanup: CleanupSection = field(default_factory=lambda: CleanupSection())

    @property
    def output_graph_dir(self) -> Path:
        if not self.static_path:
            return None
        return self.static_path.joinpath("output_graph")

    def to_dict(self) -> dict:
        _dict = self.__dict__
        _dict["project"] = self.project.__dict__
        _dict["network"] = self.network.__dict__
        _dict["origins_destinations"] = self.origins_destinations.__dict__
        _dict["isolation"] = self.isolation.__dict__
        _dict["hazard"] = self.hazard.__dict__
        _dict["cleanup"] = self.cleanup.__dict__
        return _dict

    @classmethod
    def from_ini_file(cls, ini_file: Path) -> NetworkConfigData:
        _reader = NetworkConfigDataSectionReader(ini_file)
        _reader_sections = _reader.get_sections()
        return cls(
            input_path=ini_file.parent.joinpath("input"),
            static_path=ini_file.parent.joinpath("static"),
            output_path=ini_file.parent.joinpath("output"),
            **_reader_sections,
        )
