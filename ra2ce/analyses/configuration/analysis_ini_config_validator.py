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


from ra2ce.analyses.configuration.analysis_ini_config_data_validator_base import (
    IniConfigValidatorBase,
)
from ra2ce.common.validation.validation_report import ValidationReport


class AnalysisIniConfigValidator(IniConfigValidatorBase):
    def validate(self) -> ValidationReport:
        _report = ValidationReport()
        _required_headers = ["project"]
        # Analysis are marked as [analysis1], [analysis2], ...
        _required_headers.extend([a for a in self._config.keys() if "analysis" in a])

        _report.merge(self._validate_headers(_required_headers))
        return _report


class AnalysisWithoutNetworkConfigValidator(IniConfigValidatorBase):
    def validate(self) -> ValidationReport:
        _base_report = AnalysisIniConfigValidator(self._config).validate()
        _output_network_dir = self._config.get("output", None)
        if (
            not _output_network_dir
            or not (_output_network_dir / "network.ini").is_file()
        ):
            _base_report.error(
                f"The configuration file 'network.ini' is not found at {_output_network_dir}."
                f"Please make sure to name your network settings file 'network.ini'."
            )
        return _base_report
