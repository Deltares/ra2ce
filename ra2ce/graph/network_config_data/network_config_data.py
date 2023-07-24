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


@dataclass
class ProjectSection:
    name: str = ""


@dataclass
class NetworkSection:
    directed: bool = False
    source: str = ""  # should be enum
    primary_file: str = ""  # TODO. Unclear whether this is `Path` or `list[Path]`
    diversion_file: str = ""  # TODO. Unclear whether this is `Path` or `list[Path]`
    file_id: str = ""
    polygon: str = ""  # TODO. Unclear whether this is `str`` or `Path`
    network_type: str = ""  # Should be enum
    road_types: list[str] = field(default_factory=list)
    save_shp: bool = False


@dataclass
class OriginsDestinationsSection:
    origins: Path = None
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
    hazard_map: list[Path] = field(default_factory=list)
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
