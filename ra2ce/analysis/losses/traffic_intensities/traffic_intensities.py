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
    link_id: list[int | tuple[int, int]] = field(default_factory=list)
    intensities: dict[tuple[PartOfDayEnum, TripPurposeEnum], list[int]] = field(
        default_factory=dict
    )

    def get_intensity(
        self,
        link_id: int | tuple[int, int],
        part_of_day: PartOfDayEnum,
        trip_purpose: TripPurposeEnum,
    ) -> int:
        if isinstance(link_id, tuple):
            return max(
                self.get_intensity(_id, part_of_day, trip_purpose) for _id in link_id
            )
        return self.intensities[(part_of_day, trip_purpose)][
            self.link_id.index(link_id)
        ]

    def get_intensities(
        self,
        link_ids: list[int | tuple[int, int]],
        part_of_day: PartOfDayEnum,
        trip_purpose: TripPurposeEnum,
    ) -> list[int]:
        return list(
            self.get_intensity(_link_id, part_of_day, trip_purpose)
            for _link_id in link_ids
        )
