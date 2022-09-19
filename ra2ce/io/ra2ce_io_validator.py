import logging
from pathlib import Path
from typing import Any, List, Protocol


def available_checks():
    """List of available analyses in RA2CE."""
    list_indirect_analyses = [
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
    list_direct_analyses = ["direct", "effectiveness_measures"]

    return list_indirect_analyses, list_direct_analyses


class ValidationReport:
    def __init__(self) -> None:
        self._errors = []
        self._warns = []

    def error(self, error_mssg: str) -> None:
        logging.error(error_mssg)
        self._errors.append(error_mssg)

    def warn(self, warn_mssg: str) -> None:
        logging.warning(warn_mssg)
        self._warns.append(warn_mssg)

    def is_valid(self) -> bool:
        return not any(self._errors)

    def merge(self, with_report: Any) -> None:
        """
        Merges a given report with the current one.

        Args:
            with_report (Any): ValidationReport that will be merged.
        """
        self._errors.extend(with_report._errors)
        self._warns.extend(with_report._warns)


class Ra2ceIoValidator(Protocol):
    def validate(self) -> ValidationReport:
        pass


class IniConfigurationPathValidator(Ra2ceIoValidator):
    def __init__(
        self,
        config_data: dict,
        config_property_name: str,
        path_values: str,
        input_dirs: List[Path],
    ) -> None:
        self.list_paths = []
        self._config = config_data
        self._config_property_name = config_property_name
        self._path_values = path_values
        self._input_dirs = input_dirs

    def validate(self) -> ValidationReport:
        # Check if the path is an absolute path or a file name that is placed in the right folder
        _report = ValidationReport()
        for path_value in self._path_values.split(","):
            path_value = Path(path_value)
            if path_value.is_file():
                self.list_paths.append(path_value)
                continue

            _project_name_dir = (
                self._config["root_path"] / self._config["project"]["name"]
            )
            abs_path = (
                _project_name_dir
                / "static"
                / self._input_dirs[self._config_property_name]
                / path_value
            )
            try:
                assert abs_path.is_file()
            except AssertionError:
                abs_path = (
                    _project_name_dir
                    / "input"
                    / self._input_dirs[self._config_property_name]
                    / path_value
                )

            if not abs_path.is_file():
                _report.error(
                    "Wrong input to property [ {} ], file does not exist: {}".format(
                        self._config_property_name, abs_path
                    )
                )
                _report.error(
                    "If no file is needed, please insert value - None - for property - {} -".format(
                        self._config_property_name
                    )
                )
            else:
                self.list_paths.append(abs_path)

        return _report


class IniConfigurationValidatorBase(Ra2ceIoValidator):
    def __init__(self, config_data: dict) -> None:
        self._config = config_data

    def _validate_headers(self, required_headers: List[str]) -> ValidationReport:
        _report = ValidationReport()

        def _check_header(header: str) -> None:
            if not header in self._config.keys():
                _report.error(
                    f"Property [ {header} ] is not configured. Add property [ {header} ] to the *.ini file. "
                )

        list(map(_check_header, required_headers))
        if not _report.is_valid():
            return _report
        required_headers.append("isolation")
        # check if properties have correct input
        # TODO: Decide whether also the non-used properties must be checked or those are not checked
        # TODO: Decide how to check for multiple analyses (analysis1, analysis2, etc)
        _indirect_analysis_list, _direct_analysis_list = available_checks()
        _list_analysis = _indirect_analysis_list + _direct_analysis_list
        _expected_values = {
            "source": ["OSM PBF", "OSM download", "shapefile", "pickle"],
            "polygon": ["file", None],
            "directed": [True, False, None],
            "network_type": ["walk", "bike", "drive", "drive_service", "all", None],
            "road_types": [
                "motorway",
                "motorway_link",
                "trunk",
                "trunk_link",
                "primary",
                "primary_link",
                "secondary",
                "secondary_link",
                "tertiary",
                "tertiary_link",
                "unclassified",
                "residential",
                "road",
                None,
            ],
            "origins": ["file", None],
            "destinations": ["file", None],
            "save_shp": [True, False, None],
            "save_csv": [True, False, None],
            "analysis": _list_analysis,
            "hazard_map": ["file", None],
            "aggregate_wl": ["max", "min", "mean", None],
            "weighing": ["distance", "time", None],
            "save_traffic": [True, False, None],
            "locations": ["file", None],
        }
        _input_dirs = {
            "polygon": "network",
            "hazard_map": "hazard",
            "origins": "network",
            "destinations": "network",
            "locations": "network",
        }

        for header in required_headers:
            # Now check the parameters per configured item.
            for key, value in self._config[header].items():
                if not key in _expected_values.keys():
                    continue

                if ("file" in _expected_values[key]) and (value is not None):
                    # Check if the path is an absolute path or a file name that is placed in the right folder
                    _path_validator = IniConfigurationPathValidator(
                        self._config, key, value, _input_dirs
                    )
                    _report.merge(_path_validator.validate())
                    # TODO: Technically this is wrong, a validator should not be 'formatting' data.
                    self._config[header][key] = _path_validator.list_paths
                    continue

                if key == "road_types" and (value is not None):
                    _expected_road_types = _expected_values["road_types"]
                    for road_type in value.replace(" ", "").split(","):
                        if road_type not in _expected_road_types:
                            _report.error(
                                f"Wrong road type is configured ({road_type}), has to be one or multiple of: {_expected_road_types}"
                            )
                    continue

                if value not in _expected_values[key]:
                    _report.error(
                        f"Wrong input to property [ {key} ], has to be one of: {_expected_values[key]}"
                    )

        if not _report.is_valid():
            _report.error(
                "There are inconsistencies in the *.ini file. Please consult the log file for more information: {}".format(
                    self._config["root_path"]
                    / "data"
                    / self._config["project"]["name"]
                    / "output"
                    / "RA2CE.log"
                )
            )


class NetworkIniConfigurationValidator(IniConfigurationValidatorBase):
    def _validate_shp_input(self, network_config: dict) -> None:
        """Checks if a file id is configured when using the option to create network from shapefile"""
        if (network_config["source"] == "shapefile") and (
            network_config["file_id"] is None
        ):
            self._report.error(
                "Not possible to create network - Shapefile used as source, but no file_id configured in the network.ini file"
            )

    def validate(self) -> ValidationReport:
        """Check if input properties are correct and exist."""
        _report = ValidationReport()
        _network_config = self._config.get("network", None)
        if not _network_config:
            _report.error("Network properties not present in Network ini file.")
            return _report

        # check if properties exist in settings.ini file
        _required_headers = [
            "project",
            "network",
            "origins_destinations",
            "hazard",
            "cleanup",
        ]
        self._validate_shp_input(_network_config)
        _report.merge(self._validate_headers(_required_headers))
        return _report


class AnalysisIniConfigurationValidator(IniConfigurationValidatorBase):
    def validate(self) -> ValidationReport:
        _report = ValidationReport()
        _required_headers = ["project"]
        # Analysis are marked as [analysis1], [analysis2], ...
        _required_headers.extend([a for a in self._config.keys() if "analysis" in a])

        _report.merge(self._validate_headers(_required_headers))
        return _report


class IniConfigurationValidatorFactory:
    @staticmethod
    def get_validator(config_data: dict) -> IniConfigurationValidatorBase:
        if "network" in config_data.keys():
            return NetworkIniConfigurationValidator(config_data)
        elif any([a for a in config_data.keys() if "analysis" in a]):
            return AnalysisIniConfigurationValidator(config_data)
        raise NotImplementedError()
