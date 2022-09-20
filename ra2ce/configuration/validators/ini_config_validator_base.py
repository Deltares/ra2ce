from typing import List

from ra2ce.configuration.validators.ini_config_path_validator import (
    IniConfigPathValidator,
)
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
    "analysis": IndirectAnalysisNameList + DirectAnalysisNameList,
    "hazard_map": ["file", None],
    "aggregate_wl": ["max", "min", "mean", None],
    "weighing": ["distance", "time", None],
    "save_traffic": [True, False, None],
    "locations": ["file", None],
}


class IniConfigValidatorBase(Ra2ceIoValidator):
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
        if not "isolation" in self._config.keys():
            _report.warn("Header 'isolation' not found in the configuration.")
        else:
            required_headers.append("isolation")
        # check if properties have correct input
        # TODO: Decide whether also the non-used properties must be checked or those are not checked
        # TODO: Decide how to check for multiple analyses (analysis1, analysis2, etc)
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
                    # Value should be none or a list of paths, because it already
                    # checked that it's not none, we can assume it's a list of Paths.
                    for path_value in value:
                        if not path_value.is_file():
                            _report.error(
                                f"Wrong input to property [ {key} ], file does not exist: {path_value}"
                            )
                            _report.error(
                                f"If no file is needed, please insert value - None - for property - {key} -"
                            )
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
