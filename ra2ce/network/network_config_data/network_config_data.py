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
        Identifier for the network section.
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
    primary_file: Optional[list[Path]] = field(default_factory=list)
    diversion_file: list[Path] = field(default_factory=list)
    file_id: str = ""
    link_type_column: Optional[str] = "highway"
    polygon: Optional[Path] = None
    network_type: NetworkTypeEnum = field(default_factory=lambda: NetworkTypeEnum.NONE)
    road_types: list[RoadTypeEnum] = field(default_factory=list)
    attributes_to_exclude_in_simplification: Optional[list[str]] = field(default_factory=list)
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
    """
    Data class for network configuration data.

    Holds configuration for a transport network, including paths, coordinate reference system (CRS),
    and various sections such as project details, network specifics, origins and destinations,
    isolation points, hazard information, and cleanup options.

    Parameters
    ----------
    root_path
        The root directory path for the project.
    input_path
        The input directory path for the project.
    output_path
        The output directory path for the project.
    static_path
        The static files directory path for the project.
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
    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
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
