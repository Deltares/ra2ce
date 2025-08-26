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
from typing import Optional

from pyproj import CRS

from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum


@dataclass
class ProjectSection:
    name: str = ""


@dataclass
class NetworkSection:
    """Represents a section of the transport network.

    Args:
        directed (bool): Whether the graph of the network should be directed. Default is False.
        source (SourceEnum): Source of the network data. Default is SourceEnum.INVALID.
        primary_file (Optional[list[Path]]): If source is set to SourceEnum.SHAPEFILE, provide here a list of shapefiles for the network.
        diversion_file (list[Path]): List of diversion files.
        file_id (str): Identifier for the network section.
        link_type_column (str): Name of the column that defines link type. Default 'highway'.
        polygon (Optional[Path]): If source is set to SourceEnum.OSM_DOWNLOAD, indicate the path of a shapefile polygon to clip the network.
        network_type (NetworkTypeEnum): Type of network. Default is NetworkTypeEnum.NONE.
        road_types (list[RoadTypeEnum]): List of road types included in this section.
        attributes_to_exclude_in_simplification (list[str]): List of attributes not to simplify.
        save_gpkg (bool): Whether to save a GeoPackage file of the network. Default False.
    """

    directed: bool = False
    source: SourceEnum = field(default_factory=lambda: SourceEnum.INVALID)
    primary_file: Optional[list[Path]] = field(default_factory=list)
    diversion_file: list[Path] = field(default_factory=list)
    file_id: str = ""
    link_type_column: str = "highway"
    polygon: Optional[Path] = None
    network_type: NetworkTypeEnum = field(default_factory=lambda: NetworkTypeEnum.NONE)
    road_types: list[RoadTypeEnum] = field(default_factory=list)
    attributes_to_exclude_in_simplification: list[str] = field(default_factory=list)
    save_gpkg: bool = False


@dataclass
class OriginsDestinationsSection:
    origins: Optional[Path] = None
    destinations: Optional[Path] = None
    origins_names: str = ""
    destinations_names: str = ""
    id_name_origin_destination: str = ""
    origin_count: str = ""
    origin_out_fraction: int = (
        1  # fraction of things/people going out of the origin to the destination
    )
    category: str = ""
    region: Optional[Path] = None
    region_var: str = ""


@dataclass
class IsolationSection:
    locations: str = ""  # Should be path.


@dataclass
class HazardSection:
    hazard_map: list[Path] = field(default_factory=list)
    hazard_id: str = ""
    hazard_field_name: str = ""
    aggregate_wl: AggregateWlEnum = field(default_factory=lambda: AggregateWlEnum.NONE)
    hazard_crs: str = ""
    # If False no overlay of the segmented network will be created.
    overlay_segmented_network: bool = True


@dataclass
class CleanupSection:
    snapping_threshold: bool = False
    pruning_threshold: bool = False
    segmentation_length: float = float("nan")
    merge_lines: bool = False
    cut_at_intersections: bool = False
    delete_duplicate_nodes: bool = False


@dataclass
class NetworkConfigData(ConfigDataProtocol):
    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    # CRS is not yet supported in the ini file, it might be relocated to a subsection.
    crs: CRS = field(default_factory=lambda: CRS.from_user_input(4326))
    project: ProjectSection = field(default_factory=ProjectSection)
    network: NetworkSection = field(default_factory=NetworkSection)
    origins_destinations: OriginsDestinationsSection = field(
        default_factory=OriginsDestinationsSection
    )
    isolation: IsolationSection = field(default_factory=IsolationSection)
    hazard: HazardSection = field(default_factory=HazardSection)
    cleanup: CleanupSection = field(default_factory=CleanupSection)

    @property
    def output_graph_dir(self) -> Optional[Path]:
        if not self.static_path:
            return None
        return self.static_path.joinpath("output_graph")

    @property
    def network_dir(self) -> Optional[Path]:
        if not self.static_path:
            return None
        return self.static_path.joinpath("network")

    @staticmethod
    def get_data_output(ini_file: Path) -> Path:
        return ini_file.parent.joinpath("output")

    def to_dict(self) -> dict:
        _dict = self.__dict__
        _dict["crs"] = self.crs.to_epsg()
        _dict["project"] = self.project.__dict__
        _dict["network"] = self.network.__dict__
        _dict["origins_destinations"] = self.origins_destinations.__dict__
        _dict["isolation"] = self.isolation.__dict__
        _dict["hazard"] = self.hazard.__dict__
        _dict["cleanup"] = self.cleanup.__dict__
        return _dict
