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
from dataclasses import dataclass, field

from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum


@dataclass(kw_only=True)
class TimeValues:
    """
    Class to store the time values for different trip types.
    """

    trip_types: list[TripPurposeEnum] = field(default_factory=list)
    value_of_time: list[int] = field(default_factory=list)
    occupants: list[int] = field(default_factory=list)

    def _get_index(self, trip_type: TripPurposeEnum) -> int:
        return self.trip_types.index(trip_type)

    def get_value_of_time(self, trip_type: TripPurposeEnum) -> int:
        return self.value_of_time[self._get_index(trip_type)]

    def get_occupants(self, trip_type: TripPurposeEnum) -> int:
        return self.occupants[self._get_index(trip_type)]
