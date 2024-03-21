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
from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    NetworkSection,
    ProjectSection,
)

NetworkDictValues: dict[str, list[Any]] = {
    "polygon": ["file", None],
    "directed": [True, False, None],
    "origins": ["file", None],
    "destinations": ["file", None],
    "save_gpkg": [True, False, None],
    "save_csv": [True, False, None],
    "hazard_map": ["file", None],
    "save_traffic": [True, False, None],
    "locations": ["file", None],
}


class NetworkConfigDataValidator(Ra2ceIoValidator):
    def __init__(self, config_data: NetworkConfigData) -> None:
        self._config = config_data

    def _validate_shp_input(self, network_config: NetworkSection) -> ValidationReport:
        """Checks if a file id is configured when using the option to create network from shapefile"""
        _shp_report = ValidationReport()
        if network_config.source == SourceEnum.SHAPEFILE and not network_config.file_id:
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
        _accepted_values = ", ".join(NetworkDictValues[key])
        return (
            f"Wrong input to property [ {key} ]; has to be one of: {_accepted_values}."
        )

    def _wrong_enum(self, key: str, enum: Ra2ceEnumBase) -> str:
        # Remove last value INVALID
        _accepted_values = enum.list_valid_options()
        return (
            f"Wrong input to property [ {key} ]; has to be one of: {_accepted_values}."
        )

    def _validate_enum(self, enum: Ra2ceEnumBase, key: str) -> ValidationReport:
        _report = ValidationReport()
        if not enum.is_valid():
            _report.error(self._wrong_enum(key, enum))
        return _report

    def _validate_project_section(
        self, project_section: ProjectSection
    ) -> ValidationReport:
        _report = ValidationReport()
        if not project_section:
            _report.error("Project section not found.")
        return _report

    def _validate_network_section(
        self, network_section: NetworkSection
    ) -> ValidationReport:
        _network_report = ValidationReport()

        # Validate source
        _network_report.merge(self._validate_enum(network_section.source, "source"))

        # Validate network_type
        _network_report.merge(
            self._validate_enum(network_section.network_type, "network_type")
        )

        # Validate road types.
        if network_section.road_types and any(
            not _type.is_valid() for _type in network_section.road_types
        ):
            _network_report.error(
                f"Wrong road type(s) configured; has to be one or multiple of: {[_type.config_value for _type in network_section.road_types[0].list_valid_options()]}"
            )
        return _network_report

    def _validate_hazard_section(
        self, hazard_section: HazardSection
    ) -> ValidationReport:
        _hazard_report = ValidationReport()

        _hazard_report.merge(
            self._validate_enum(hazard_section.aggregate_wl, "aggregate_wl")
        )

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
