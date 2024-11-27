import re
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Union

from ra2ce.common.configuration.ini_configuration_reader_protocol import (
    ConfigDataReaderProtocol,
)
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    CleanupSection,
    HazardSection,
    IsolationSection,
    NetworkConfigData,
    NetworkSection,
    OriginsDestinationsSection,
    ProjectSection,
)


class NetworkConfigDataReader(ConfigDataReaderProtocol):
    _parser: ConfigParser

    def __init__(self) -> None:
        self._parser = ConfigParser(
            inline_comment_prefixes="#",
            converters={"list": lambda x: [x.strip() for x in re.split("[,|;]", x)]},
        )

    def read(self, ini_file: Path) -> NetworkConfigData:
        self._parser.read(ini_file)
        self._remove_none_values()

        _parent_dir = ini_file.parent

        _config_data = NetworkConfigData(
            root_path=_parent_dir.parent,
            input_path=_parent_dir.joinpath("input"),
            static_path=_parent_dir.joinpath("static"),
            output_path=_parent_dir.joinpath("output"),
            **self._get_sections(),
        )
        self._correct_paths(_config_data)
        return _config_data

    def _correct_paths(self, config_data: NetworkConfigData) -> None:
        """
        This method is created because we support defining Path properties with just their filename, but no relative or absolute references.
        These need to be done later on by combining the `input`, `static` or `output` paths. To avoid extra logic all over the solution,
        we can correct these paths here.

        Args:
            config_data (NetworkConfigData): The configuration data whose paths need to be corrected.
        """

        def _select_to_correct(path_value: Union[list[Path], Path]) -> bool:
            if not path_value:
                return False

            if isinstance(path_value, list):
                return _select_to_correct(path_value[0])
            return not path_value.exists()

        def _correct_list(path_root: Path, path_value_list: list[Path]) -> list[Path]:
            _corrected_list = []
            for _path_value in path_value_list:
                if not _path_value.exists():
                    _corrected_list.append(path_root.joinpath(_path_value))
                else:
                    _corrected_list.append(_path_value)
            return _corrected_list

        # Relative to network directory.
        _network_directory = config_data.static_path.joinpath("network")
        if _select_to_correct(config_data.origins_destinations.origins):
            config_data.origins_destinations.origins = _network_directory.joinpath(
                config_data.origins_destinations.origins
            )

        if _select_to_correct(config_data.origins_destinations.destinations):
            config_data.origins_destinations.destinations = _network_directory.joinpath(
                config_data.origins_destinations.destinations
            )

        if _select_to_correct(config_data.origins_destinations.region):
            config_data.origins_destinations.region = _network_directory.joinpath(
                config_data.origins_destinations.region
            )

        if _select_to_correct(config_data.network.polygon):
            config_data.network.polygon = _network_directory.joinpath(
                config_data.network.polygon
            )

        config_data.network.primary_file = _correct_list(
            _network_directory, config_data.network.primary_file
        )
        config_data.network.diversion_file = _correct_list(
            _network_directory, config_data.network.diversion_file
        )

        # Relative to hazard directory.
        _hazard_directory = config_data.static_path.joinpath("hazard")
        config_data.hazard.hazard_map = _correct_list(
            _hazard_directory, config_data.hazard.hazard_map
        )

    def _get_str_as_path(self, str_value: Union[str, Path]) -> Path:
        if str_value and not isinstance(str_value, Path):
            return Path(str_value)
        return str_value

    def _remove_none_values(self) -> None:
        # Remove 'None' from values, replace them with empty strings
        for _section in self._parser.sections():
            _keys_with_none = [
                k for k, v in self._parser[_section].items() if v == "None"
            ]
            for _key_with_none in _keys_with_none:
                self._parser[_section].pop(_key_with_none)

    def _get_sections(self) -> dict:
        return {
            "project": self.get_project_section(),
            "network": self.get_network_section(),
            "origins_destinations": self.get_origins_destinations_section(),
            "isolation": self.get_isolation_section(),
            "hazard": self.get_hazard_section(),
            "cleanup": self.get_cleanup_section(),
        }

    def get_project_section(self) -> ProjectSection:
        return ProjectSection(**self._parser["project"])

    def _get_path_list(
        self, section_name: str, property: str, fallback_opt: Any
    ) -> list[Path]:
        _value_list = self._parser.getlist(
            section_name, property, fallback=fallback_opt
        )
        return list(map(self._get_str_as_path, _value_list))

    def get_network_section(self) -> NetworkSection:
        _section = "network"
        _network_section = NetworkSection(**self._parser[_section])
        _network_section.source = SourceEnum.get_enum(
            self._parser.get(_section, "source", fallback=None)
        )
        _network_section.primary_file = self._get_path_list(
            _section, "primary_file", _network_section.primary_file
        )
        _network_section.diversion_file = self._get_path_list(
            _section, "diversion_file", _network_section.diversion_file
        )
        _network_section.directed = self._parser.getboolean(
            _section, "directed", fallback=_network_section.directed
        )
        _network_section.save_gpkg = self._parser.getboolean(
            _section, "save_gpkg", fallback=_network_section.save_gpkg
        )
        _network_section.network_type = NetworkTypeEnum.get_enum(
            self._parser.get(_section, "network_type", fallback=None)
        )
        _network_section.road_types = list(
            map(
                RoadTypeEnum.get_enum,
                self._parser.getlist(_section, "road_types", fallback=[]),
            )
        )
        _network_section.polygon = self._get_str_as_path(_network_section.polygon)
        _network_section.attributes_to_exclude_in_simplification = self._parser.getlist(
            _section, "attributes_to_exclude_in_simplification", fallback=[]
        )
        return _network_section

    def get_origins_destinations_section(self) -> OriginsDestinationsSection:
        _section = "origins_destinations"
        if _section not in self._parser:
            return OriginsDestinationsSection()

        _od_section = OriginsDestinationsSection(**self._parser[_section])
        _od_section.origin_out_fraction = self._parser.getint(
            _section, "origin_out_fraction", fallback=_od_section.origin_out_fraction
        )
        _od_section.origins = self._get_str_as_path(_od_section.origins)
        _od_section.destinations = self._get_str_as_path(_od_section.destinations)
        _od_section.region = self._get_str_as_path(_od_section.region)
        return _od_section

    def get_isolation_section(self) -> IsolationSection:
        _section = "isolation"
        if _section not in self._parser:
            return IsolationSection()

        return IsolationSection(**self._parser[_section])

    def get_hazard_section(self) -> HazardSection:
        _section = "hazard"
        if _section not in self._parser:
            return HazardSection()

        _hazard_section = HazardSection(**self._parser[_section])
        _hazard_section.hazard_map = list(
            map(
                self._get_str_as_path,
                self._parser.getlist(
                    _section, "hazard_map", fallback=_hazard_section.hazard_map
                ),
            )
        )
        _hazard_section.aggregate_wl = AggregateWlEnum.get_enum(
            self._parser.get(_section, "aggregate_wl", fallback=None)
        )

        _hazard_section.overlay_segmented_network = self._parser.getboolean(
            _section,
            "overlay_segmented_network",
            fallback=_hazard_section.overlay_segmented_network,
        )
        return _hazard_section

    def get_cleanup_section(self) -> CleanupSection:
        _section = "cleanup"
        if _section not in self._parser:
            return CleanupSection()

        _cleanup_section = CleanupSection()
        _cleanup_section.snapping_threshold = self._parser.getboolean(
            _section,
            "snapping_threshold",
            fallback=_cleanup_section.snapping_threshold,
        )
        _cleanup_section.pruning_threshold = self._parser.getboolean(
            _section,
            "pruning_threshold",
            fallback=_cleanup_section.pruning_threshold,
        )
        _cleanup_section.segmentation_length = self._parser.getfloat(
            _section,
            "segmentation_length",
            fallback=_cleanup_section.segmentation_length,
        )
        _cleanup_section.merge_lines = self._parser.getboolean(
            _section, "merge_lines", fallback=_cleanup_section.merge_lines
        )
        _cleanup_section.cut_at_intersections = self._parser.getboolean(
            _section,
            "cut_at_intersections",
            fallback=_cleanup_section.cut_at_intersections,
        )
        _cleanup_section.delete_duplicate_nodes = self._parser.getboolean(
            _section,
            "delete_duplicate_nodes",
            fallback=_cleanup_section.delete_duplicate_nodes,
        )
        return _cleanup_section
