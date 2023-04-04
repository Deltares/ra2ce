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


from pathlib import Path
from typing import Any, Dict, List, Optional

from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol
from ra2ce.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.validation.validation_report import ValidationReport

IndirectAnalysisNameList: List[str] = [
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
DirectAnalysisNameList: List[str] = ["direct", "effectiveness_measures"]
_expected_values: Dict[str, List[Any]] = {
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
    "analysis": IndirectAnalysisNameList + DirectAnalysisNameList,
    "hazard_map": ["file", None],
    "aggregate_wl": ["max", "min", "mean", None],
    "weighing": ["distance", "time", None],
    "save_traffic": [True, False, None],
    "locations": ["file", None],
}


class IniConfigValidatorBase(Ra2ceIoValidator):
    def __init__(self, config_data: IniConfigDataProtocol) -> None:
        self._config = config_data

    def validate(self) -> ValidationReport:
        raise NotImplementedError()

    def _validate_files(
        self, header: str, path_value_list: Optional[List[Path]]
    ) -> ValidationReport:
        # Value should be none or a list of paths, because it already
        # checked that it's not none, we can assume it's a list of Paths.
        _files_report = ValidationReport()
        if not path_value_list:
            return _files_report
        for path_value in path_value_list:
            if not path_value.is_file():
                _files_report.error(
                    f"Wrong input to property [ {header} ], file does not exist: {path_value}"
                )
                _files_report.error(
                    f"If no file is needed, please insert value - None - for property - {header} -"
                )
        return _files_report

    def _validate_road_types(self, road_type_value: str) -> ValidationReport:
        _road_types_report = ValidationReport()
        if not road_type_value:
            return _road_types_report
        _expected_road_types = _expected_values["road_types"]
        _road_type_value_list = road_type_value.replace(" ", "").split(",")
        for road_type in _road_type_value_list:
            if road_type not in _expected_road_types:
                _road_types_report.error(
                    f"Wrong road type is configured ({road_type}), has to be one or multiple of: {_expected_road_types}"
                )
        return _road_types_report

    def _validate_headers(self, required_headers: List[str]) -> ValidationReport:
        _report = ValidationReport()
        _available_keys: List[str] = self._config.keys()

        def _check_header(header: str) -> None:
            if header not in _available_keys:
                _report.error(
                    f"Property [ {header} ] is not configured. Add property [ {header} ] to the *.ini file. "
                )

        list(map(_check_header, required_headers))
        if not _report.is_valid():
            return _report

        # check if properties have correct input
        # TODO: Decide whether also the non-used properties must be checked or those are not checked
        # TODO: Decide how to check for multiple analyses (analysis1, analysis2, etc)

        for header in required_headers:
            # Now check the parameters per configured item.
            for key, value in self._config[header].items():
                if key not in _expected_values.keys():
                    continue
                _expected_values_list: List[Any] = _expected_values[key]
                if "file" in _expected_values_list:
                    # Value should be none or a list of paths, because it already
                    # checked that it's not none, we can assume it's a list of Paths.
                    _report.merge(self._validate_files(key, value))
                    continue

                if key == "road_types":
                    _report.merge(self._validate_road_types(value))
                    continue

                if value not in _expected_values_list:
                    _report.error(
                        f"Wrong input to property [ {key} ], has to be one of: {_expected_values_list}"
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
