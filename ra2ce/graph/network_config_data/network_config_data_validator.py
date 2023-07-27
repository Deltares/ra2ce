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

from typing import Any
from ra2ce.common.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.common.validation.validation_report import ValidationReport
from ra2ce.graph.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    NetworkSection,
    ProjectSection,
)

NetworkDictValues: dict[str, list[Any]] = {
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
    "hazard_map": ["file", None],
    "aggregate_wl": ["max", "min", "mean", None],
    "weighing": ["distance", "time", None],
    "save_traffic": [True, False, None],
    "locations": ["file", None],
}


class NetworkConfigDataValidator(Ra2ceIoValidator):
    def __init__(self, config_data: NetworkConfigData) -> None:
        self._config = config_data

    def _validate_shp_input(self, network_config: NetworkSection) -> ValidationReport:
        """Checks if a file id is configured when using the option to create network from shapefile"""
        _shp_report = ValidationReport()
        if network_config.source == "shapefile" and not network_config.file_id:
            _shp_report.error(
                "Not possible to create network - Shapefile used as source, but no file_id configured in the network.ini file"
            )
        return _shp_report

    def validate(self) -> ValidationReport:
        """Check if input properties are correct and exist."""
        _report = ValidationReport()
        if not self._config.network:
            _report.error("Network properties not present in Network ini file.")
            return _report

        # check if properties exist in settings.ini file
        _report.merge(self._validate_shp_input(self._config.network))
        _report.merge(self._validate_sections())
        return _report

    def _wrong_value(self, key: str) -> str:
        _accepted_values = ",".join(NetworkDictValues[key])
        return (
            f"Wrong input to property [ {key} ], has to be one of: {_accepted_values}."
        )

    def _validate_project_section(
        self, project_section: ProjectSection
    ) -> ValidationReport:
        _report = ValidationReport()
        if not project_section:
            _report.error(self._report_section_not_found("project"))
        return _report

    def _validate_network_section(
        self, network_section: NetworkSection
    ) -> ValidationReport:
        _network_report = ValidationReport()

        # Validate source
        if (
            network_section.source
            and network_section.source not in NetworkDictValues["source"]
        ):
            _network_report.error(self._wrong_value("source"))

        # Validate network_type
        if (
            network_section.network_type
            and network_section.network_type not in NetworkDictValues["network_type"]
        ):
            _network_report.error(self._wrong_value("network_type"))

        # Validate road types.
        _expected_road_types = NetworkDictValues["road_types"]
        for road_type in filter(
            lambda x: x not in _expected_road_types, network_section.road_types
        ):
            _network_report.error(
                f"Wrong road type is configured ({road_type}), has to be one or multiple of: {_expected_road_types}"
            )
        return _network_report

    def _validate_hazard_section(
        self, hazard_section: HazardSection
    ) -> ValidationReport:
        _hazard_report = ValidationReport()

        if not hazard_section.aggregate_wl:
            return _hazard_report

        if hazard_section.aggregate_wl not in NetworkDictValues["aggregate_wl"]:
            _hazard_report.error(self._wrong_value("aggregate_wl"))

        return _hazard_report

    def _validate_sections(self) -> ValidationReport:
        _report = ValidationReport()
        _available_keys = self._config.__dict__.keys()
        _required_sections = [
            "project",
            "network",
            "origins_destinations",
            "hazard",
            "cleanup",
        ]
        for _required_section in _required_sections:
            if _required_section not in _available_keys:
                _report.error(
                    f"Section [ {_required_section} ] is not configured. Add section [ {_required_section} ] to the *.ini file. "
                )

        if not _report.is_valid():
            return _report

        _report.merge(self._validate_project_section(self._config.project))
        _report.merge(self._validate_network_section(self._config.network))
        _report.merge(self._validate_hazard_section(self._config.hazard))

        return _report
