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

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    DamagesAnalysisNameList,
    LossesAnalysisNameList,
)
from ra2ce.common.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.common.validation.validation_report import ValidationReport
from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase
from ra2ce.network.network_config_data.network_config_data_validator import (
    NetworkDictValues,
)

AnalysisNetworkDictValues = NetworkDictValues | {
    "analysis": LossesAnalysisNameList + DamagesAnalysisNameList
}


class AnalysisConfigDataValidator(Ra2ceIoValidator):
    def __init__(self, config_data: AnalysisConfigData) -> None:
        self._config = config_data

    def _validate_header(self, header: Any) -> ValidationReport:
        _report = ValidationReport()

        if isinstance(header, list):
            for _item in header:
                _report.merge(self._validate_header(_item))
        else:
            # check keys with predescribed values
            for key, value in header.__dict__.items():
                if not value:
                    continue
                if isinstance(value, Ra2ceEnumBase):
                    # enumerations
                    _expected_values_list = value.list_valid_options()
                else:
                    # other items with limited value options (should become enumerations)
                    if key not in AnalysisNetworkDictValues.keys():
                        continue
                    _expected_values_list = AnalysisNetworkDictValues[key]
                if value not in _expected_values_list:
                    _report.error(
                        f"Wrong input to property [ {key} ]; has to be one of: {_expected_values_list}."
                    )

        return _report

    def _validate_headers(self, required_headers: list[str]) -> ValidationReport:
        _report = ValidationReport()
        _available_keys = self._config.__dict__.keys()

        def _check_header(header: str) -> None:
            """
            Check if the section is provided and non-empty

            Args:
                header (str): section name
            """
            if header not in _available_keys or not getattr(self._config, header):
                _report.error(
                    f"Property [ {header} ] is not configured. Add property [ {header} ] to the *.ini file. "
                )

        list(map(_check_header, required_headers))
        if not _report.is_valid():
            return _report

        # check if properties have correct input
        # TODO: Decide whether also the non-used properties must be checked or those are not checked

        for header in required_headers:
            # Now check the parameters per configured item.
            _attr = getattr(self._config, header)
            if not _attr:
                continue
            else:
                _report.merge(self._validate_header(_attr))

        if not _report.is_valid():
            _report.error(
                "There are inconsistencies in the *.ini file. Please consult the log file for more information: {}.".format(
                    self._config.output_path.joinpath("RA2CE.log")
                )
            )

        return _report

    def validate(self) -> ValidationReport:
        _report = ValidationReport()
        _required_headers = ["project", "analyses"]

        _report.merge(self._validate_headers(_required_headers))
        return _report
