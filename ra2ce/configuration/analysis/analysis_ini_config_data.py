"""
GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Deltares

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


from __future__ import annotations

from ra2ce.configuration.analysis.analysis_ini_config_validator import (
    AnalysisIniConfigValidator,
    AnalysisWithoutNetworkConfigValidator,
)
from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol


class AnalysisIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        raise NotImplementedError("Implement in concrete classes")

    def is_valid(self) -> bool:
        raise NotImplementedError("Implement in concrete classes")


class AnalysisWithNetworkIniConfigData(AnalysisIniConfigData):
    @classmethod
    def from_dict(cls, dict_values) -> AnalysisWithNetworkIniConfigData:
        _new_analysis_ini_config_data = cls()
        _new_analysis_ini_config_data.update(**dict_values)
        return _new_analysis_ini_config_data

    def is_valid(self) -> bool:
        _validation_report = AnalysisIniConfigValidator(self).validate()
        return _validation_report.is_valid()


class AnalysisWithoutNetworkIniConfigData(AnalysisIniConfigData):
    @classmethod
    def from_dict(cls, dict_values) -> AnalysisWithoutNetworkIniConfigData:
        _new_analysis_ini_config_data = cls()
        _new_analysis_ini_config_data.update(**dict_values)
        return _new_analysis_ini_config_data

    def is_valid(self) -> bool:
        _validation_report = AnalysisWithoutNetworkConfigValidator(self).validate()
        return _validation_report.is_valid()
