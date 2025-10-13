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
from dataclasses import fields
from typing import Callable


def with_legacy_mappers(cls):
    """
    Method to be used as a decorator to inject the inner defined (class)
    methods in the assigned (data)class objects.

    E.g.:
    @with_legacy_mappers
    @dataclass
    class ConcreteLegacyIniMapper:
        name: str
    """

    @classmethod
    def from_ini_file(cls, **kwargs):
        """
        Excludes any unknown fields from the input dictionary
        and initializes the dataclass object.
        """
        _field_names = set([f.name for f in fields(cls)])
        return cls(**{k: v for k, v in kwargs.items() if k in _field_names})

    setattr(cls, "from_ini_file", from_ini_file)  # add new method
    return cls