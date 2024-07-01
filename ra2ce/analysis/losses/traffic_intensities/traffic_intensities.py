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

from ra2ce.analysis.analysis_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum


@dataclass(kw_only=True)
class TrafficIntensities:
    """
    Class to store the traffic intensities per hour for a specific part of day
    for different trip purposes.
    """

    link_id: list[int | tuple[int, int]] = field(default_factory=list)
    intensities: dict[tuple[PartOfDayEnum, TripPurposeEnum], list[int]] = field(
        default_factory=dict
    )

    def calculate_intensity(
        self,
        link_id: int | tuple[int, int],
        part_of_day: PartOfDayEnum,
        trip_purpose: TripPurposeEnum,
    ) -> int:
        """
        Calculate the traffic intensity for a specific link
        for a specific part of day for a specific trip purpose.

        For a simplified graph, the link_id could be a tuple of link_ids.
        In that case the maximum intensity of the links is returned.

        Args:
            link_id (int | tuple[int, int]): The link id(s)
            part_of_day (PartOfDayEnum): Part of the day
            trip_purpose (TripPurposeEnum): Trip purpose

        Returns:
            int: The intensity for that (set of) link(s)
        """
        if isinstance(link_id, tuple):
            return max(
                self.calculate_intensity(_id, part_of_day, trip_purpose)
                for _id in link_id
            )
        return self.intensities[(part_of_day, trip_purpose)][
            self.link_id.index(link_id)
        ]
