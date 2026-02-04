"""
                GNU GENERAL PUBLIC LICENSE
                  Version 3, 29 June 2007

Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
Copyright (C) 2023-2026 Stichting Deltares

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
    """
    Represents a section of the transport network.

    Parameters
    ----------
    directed
        Whether the graph of the network should be directed. Default is ``False``.
    source
        Source of the network data. Default is ``SourceEnum.INVALID``.
    primary_file
        If ``source`` is set to ``SourceEnum.SHAPEFILE``, provide a list of shapefiles for the network.
    diversion_file
        List of diversion files.
    file_id
        field name of the ID attribute in the shapefile for network creating with a shapefile as source.
    link_type_column
        Attribute name in a GeoDataFrame or shapefile that defines link type (e.g. type of road). Default is ``'highway'``.
    polygon
        If ``source`` is set to ``SourceEnum.OSM_DOWNLOAD``, path to a shapefile polygon to clip the network.
    network_type
        Type of network. Default is ``NetworkTypeEnum.NONE``.
    road_types
        List of road types to download from OSM if ``source`` is set to ``SourceEnum.OSM_DOWNLOAD``.
    attributes_to_exclude_in_simplification
        List of attributes not to simplify.
    save_gpkg
        Whether to save a GeoPackage file of the network in the output_graph folder. Default is ``False``.
    """

    directed: bool = False
    source: SourceEnum = field(default_factory=lambda: SourceEnum.INVALID)
    primary_file: Optional[Path] = None
    diversion_file: Optional[Path] = None
    file_id: str = ""
    link_type_column: Optional[str] = "highway"
    polygon: Optional[Path] = None
    network_type: NetworkTypeEnum = field(default_factory=lambda: NetworkTypeEnum.NONE)
    road_types: list[RoadTypeEnum] = field(default_factory=list)
    attributes_to_exclude_in_simplification: Optional[list[str]] = field(
        default_factory=list
    )
    save_gpkg: bool = False
    reuse_network_output: bool = False


@dataclass
class OriginsDestinationsSection:
    """
    Parametrization for origins and destinations.

    Parameters
    ----------
    origins
        Path to a shapefile or other supported file containing origin points.
    destinations
        Path to a shapefile or other supported file containing destination points.
    origins_names
        Shortcut name for the origins, used in output files.
    destinations_names
        Shortcut name for the destinations, used in output files.
    id_name_origin_destination
        Field name of the ID attribute in both the origins and destinations files. Mandatory field.
    origin_count
        Field name of the attribute in the origins file that contains the count of things/people at the origin. Mandatory field.
    origin_out_fraction
        Fraction of things/people going out of the origin to the destination. Default is 1.
    category
        (Field name of the attribute in the origins and destinations files that contains the category of the origin/destination.
    region
        (Optional) Path to a shapefile or other supported file containing the region polygon.
    region_var
        (Optional) Field name of the attribute in the region file that contains the region variable.
    """

    origins: Optional[Path] = None
    destinations: Optional[Path] = None
    origin_count: Optional[str] = None
    origin_out_fraction: int = (
        1  # fraction of things/people going out of the origin to the destination
    )
    category: Optional[str] = ""
    region: Optional[Path] = None
    region_var: Optional[str] = ""


@dataclass
class IsolationSection:
    locations: str = ""  # Should be path.


@dataclass
class HazardSection:
    """
    Represents a section of the transport network.

    Parameters
    ----------
    hazard_map
        list of path to raster files representing the hazard maps, for which the hazard overlay will be performed on the network.
    hazard_id
        Identifier for the hazard section.
    hazard_field_name
        Name of the field in the hazard map to be used for the overlay.
    aggregate_wl
        If a network link intersects multiple cells of the hazard map, choose which method to aggregate hazard intensity levels. Default is ``AggregateWlEnum.NONE``.
    hazard_crs
        Coordinate reference system of the hazard maps.
    overlay_segmented_network
        If False no overlay of the segmented network will be created. Default is ``True``.
    """

    hazard_map: list[Path] = field(default_factory=list)
    hazard_id: Optional[str] = ""
    hazard_field_name: Optional[str] = ""
    aggregate_wl: AggregateWlEnum = field(default_factory=lambda: AggregateWlEnum.NONE)
    hazard_crs: str = ""
    # If False no overlay of the segmented network will be created.
    overlay_segmented_network: Optional[bool] = True


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
    """
    Data class for network configuration data.

    Holds configuration for a transport network, including paths, coordinate reference system (CRS),
    and various sections such as project details, network specifics, origins and destinations,
    isolation points, hazard information, and cleanup options.

    Parameters
    ----------
    root_path
        The root directory path for the project.
    static_path
        The static files directory path for the project. Recommended to be: root_path/static.
    crs : CRS, default=EPSG:4326
        The coordinate reference system used in the project.
    project
        Section containing project details.
    network
        Section containing network specifics.
    origins_destinations
        Section containing origins and destinations details. Required only for analysis types that need about accessibility.
    isolation
        Section containing isolation points details. Required only for analyses about isolated locations.
    hazard
        Section containing hazard information. Required only for analysis with a hazard component/map.
    cleanup
        Section containing cleanup options.
    """

    root_path: Path = None
    static_path: Path = None
    # CRS is not yet supported in the ini file, it might be relocated to a subsection.
    crs: Optional[CRS] = field(default_factory=lambda: CRS.from_user_input(4326))
    project: Optional[ProjectSection] = field(default_factory=ProjectSection)
    network: NetworkSection = field(default_factory=NetworkSection)
    origins_destinations: Optional[OriginsDestinationsSection] = field(
        default_factory=OriginsDestinationsSection
    )
    isolation: Optional[IsolationSection] = field(default_factory=IsolationSection)
    hazard: Optional[HazardSection] = field(default_factory=HazardSection)
    cleanup: Optional[CleanupSection] = field(default_factory=CleanupSection)

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
