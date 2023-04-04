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


from __future__ import annotations

from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol
from ra2ce.configuration.network.network_ini_config_validator import (
    NetworkIniConfigurationValidator,
)


class NetworkIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> NetworkIniConfigData:
        _new_network_ini_config_data = cls()
        _new_network_ini_config_data.update(**dict_values)
        return _new_network_ini_config_data

    def is_valid(self) -> bool:
        _report = NetworkIniConfigurationValidator(self).validate()
        return _report.is_valid()
