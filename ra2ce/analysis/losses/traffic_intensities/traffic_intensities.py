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
from operator import itemgetter

from ra2ce.analysis.analysis_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum


@dataclass(kw_only=True)
class TrafficIntensities:
    link_id: list[int] = field(default_factory=list)
    intensities: dict[tuple[PartOfDayEnum, TripPurposeEnum], list[int]] = field(
        default_factory=dict
    )

    def get_intensity(
        self,
        link_ids: list[int],
        part_of_day: PartOfDayEnum,
        trip_purpose: TripPurposeEnum,
    ) -> int:
        _idx = list(
            filter(lambda x: self.link_id[x] in link_ids, range(len(self.link_id)))
        )
        if not _idx:
            return 0
        return sum(itemgetter(*_idx)(self.intensities[(part_of_day, trip_purpose)]))
