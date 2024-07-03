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

    time_values: dict[TripPurposeEnum, tuple[int, int]] = field(default_factory=dict)

    def get_value_of_time(self, trip_type: TripPurposeEnum) -> int:
        """
        Get the value of time for a given trip type.

        Args:
            trip_type (TripPurposeEnum): The type of the trip.

        Returns:
            int: The value of time.
        """
        return self.time_values[trip_type][0]

    def get_occupants(self, trip_type: TripPurposeEnum) -> int:
        """
        Get the occupants for a given trip type.

        Args:
            trip_type (TripPurposeEnum): The type of the trip.

        Returns:
            int: The occupants.
        """
        return self.time_values[trip_type][1]
