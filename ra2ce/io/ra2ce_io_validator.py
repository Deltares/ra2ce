# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
@author: M. Kwant, Deltares
"""

import logging
import sys
from pathlib import Path
from typing import Any, List, Protocol, Tuple

import future


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


list_indirect_analyses, list_direct_analyses = available_checks()


def input_validation(config):
    """Check if input properties are correct and exist."""

    # check if properties exist in settings.ini file
    check_headers = ["project"]
    check_headers.extend([a for a in config.keys() if "analysis" in a])

    if "network" in config.keys():
        check_shp_input(config["network"])
        check_headers.extend(
            ["network", "origins_destinations", "hazard", "cleanup", "isolation"]
        )

    for k in check_headers:
        if k == "isolation":
            # The isolation header is not required but needs to be checked with the code underneath.
            continue

        if k not in config.keys():
            logging.error(
                "Property [ {} ] is not configured. Add property [ {} ] to the *.ini file. ".format(
                    k, k
                )
            )
            sys.exit()

    # check if properties have correct input
    # TODO: Decide whether also the non-used properties must be checked or those are not checked
    # TODO: Decide how to check for multiple analyses (analysis1, analysis2, etc)
    list_analyses = list_direct_analyses + list_indirect_analyses
    check_answer = {
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
        "analysis": list_analyses,
        "hazard_map": ["file", None],
        "aggregate_wl": ["max", "min", "mean", None],
        "weighing": ["distance", "time", None],
        "save_traffic": [True, False, None],
        "locations": ["file", None],
    }
    input_dirs = {
        "polygon": "network",
        "hazard_map": "hazard",
        "origins": "network",
        "destinations": "network",
        "locations": "network",
    }

    error = False
    for key in config:
        # First check the headers.
        if key in check_headers:
            # Now check the parameters per configured item.
            for item in config[key]:
                if item in check_answer:
                    if ("file" in check_answer[item]) and (
                        config[key][item] is not None
                    ):
                        # Check if the path is an absolute path or a file name that is placed in the right folder
                        config[key][item], error = check_paths(
                            config, key, item, input_dirs, error
                        )
                        continue

                    if item == "road_types" and (config[key][item] is not None):
                        for road_type in config[key][item].replace(" ", "").split(","):
                            if road_type not in check_answer["road_types"]:
                                logging.error(
                                    "Wrong road type is configured ({}), has to be one or multiple of: {}".format(
                                        road_type, check_answer["road_types"]
                                    )
                                )
                                error = True
                        continue

                    if config[key][item] not in check_answer[item]:
                        logging.error(
                            "Wrong input to property [ {} ], has to be one of: {}".format(
                                item, check_answer[item]
                            )
                        )
                        error = True

    # Quit if error
    if error:
        logging.error(
            "There are inconsistencies in the *.ini file. Please consult the log file for more information: {}".format(
                config["root_path"]
                / "data"
                / config["project"]["name"]
                / "output"
                / "RA2CE.log"
            )
        )
        sys.exit()

    return config


def check_paths(config, key, item, input_dirs, error):
    # Check if the path is an absolute path or a file name that is placed in the right folder
    list_paths = []
    for p in config[key][item].split(","):
        p = Path(p)
        if not p.is_file():
            abs_path = (
                config["root_path"]
                / config["project"]["name"]
                / "static"
                / input_dirs[item]
                / p
            )
            try:
                assert abs_path.is_file()
            except AssertionError:
                abs_path = (
                    config["root_path"]
                    / config["project"]["name"]
                    / "input"
                    / input_dirs[item]
                    / p
                )

            if not abs_path.is_file():
                logging.error(
                    "Wrong input to property [ {} ], file does not exist: {}".format(
                        item, abs_path
                    )
                )
                logging.error(
                    "If no file is needed, please insert value - None - for property - {} -".format(
                        item
                    )
                )
                error = True
            else:
                list_paths.append(abs_path)
        else:
            list_paths.append(p)
    return list_paths, error


def check_shp_input(config):
    """Checks if a file id is configured when using the option to create network from shapefile"""
    if (config["source"] == "shapefile") and (config["file_id"] is None):
        logging.error(
            "Not possible to create network - Shapefile used as source, but no file_id configured in the network.ini file"
        )
        sys.exit()


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
        return any(self._errors)

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
        config_header: str,
        config_key: str,
        input_dirs: List[Path],
    ) -> None:
        self.list_paths = []
        self._config_data = config_data
        self._config_header = config_header
        self._config_key = config_key
        self._input_dirs = input_dirs

    def validate(self) -> ValidationReport:
        # Check if the path is an absolute path or a file name that is placed in the right folder
        _report = ValidationReport()
        _path_values = self._config_data[self._config_header][self._config_key]

        for path_value in _path_values.split(","):
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
                / self._input_dirs[self._config_key]
                / path_value
            )
            try:
                assert abs_path.is_file()
            except AssertionError:
                abs_path = (
                    _project_name_dir
                    / "input"
                    / self._input_dirs[self._config_key]
                    / path_value
                )

            if not abs_path.is_file():
                _report.error(
                    "Wrong input to property [ {} ], file does not exist: {}".format(
                        self._config_key, abs_path
                    )
                )
                _report.error(
                    "If no file is needed, please insert value - None - for property - {} -".format(
                        self._config_key
                    )
                )
            else:
                self.list_paths.append(abs_path)

        return _report


class NetworkIniConfigurationValidatorBase(Ra2ceIoValidator):
    def __init__(self, network_data: dict) -> None:
        self._config = network_data

    def validate(self) -> ValidationReport:
        """Check if input properties are correct and exist."""
        _report = ValidationReport()
        if not self._config.get("network", None):
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
        check_shp_input(self._config["network"])

        def _check_header(header: str) -> None:
            if not header in self._config.keys():
                _report.error(
                    f"Property [ {header} ] is not configured. Add property [ {header} ] to the *.ini file. "
                )

        list(map(_check_header, _required_headers))
        if not _report.is_valid():
            return _report
        _required_headers.append("isolation")

        # check if properties have correct input
        # TODO: Decide whether also the non-used properties must be checked or those are not checked
        # TODO: Decide how to check for multiple analyses (analysis1, analysis2, etc)
        _list_analysis = list_direct_analyses + list_indirect_analyses
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

        for header in _required_headers:
            # Now check the parameters per configured item.
            for key, value in self._config[header].items():
                if not key in _expected_values.keys():
                    continue

                if ("file" in _expected_values[key]) and (value is not None):
                    # Check if the path is an absolute path or a file name that is placed in the right folder
                    _path_validator = IniConfigurationPathValidator(
                        self._config, header, key, _input_dirs
                    )
                    _report.merge(_path_validator.validate())
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

        return _report
