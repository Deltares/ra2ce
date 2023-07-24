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

from typing import Any


class IniConfigDataProtocol(dict):  # pragma: no cover
    """
    IniConfigProtocol, for now it's a dictionary until we start mapping its entries to real properties.
    Then we will transform it into a protocol.
    """

    @classmethod
    def from_dict(cls, dict_values: dict) -> IniConfigDataProtocol:
        """
        Initializes the `IniConfigDataProtocol` concrete class based on the given values.

        Args:
            dict_values (dict): Dictionary of values to map into the `IniConfigDataProtocol`

        Returns:
            IniConfigDataProtocol:  Initialized object.
        """
        pass

    def is_valid(self) -> bool:
        """
        Validates the current instance.

        Returns:
            bool: Whether it is valid or not.
        """
        pass
