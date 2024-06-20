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

from ast import literal_eval
from collections import defaultdict
from dataclasses import dataclass, field

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass
class RoadTypeEntry:
    road_type: RoadTypeEnum | list[RoadTypeEnum]

    def __str__(self) -> str:
        """
        Override the str function to make it writeable as key in the CSV.
        """
        if isinstance(self.road_type, list):
            return str([x.config_value for x in self.road_type])
        return self.road_type.config_value

    def __hash__(self) -> int:
        """
        Override the hash function to make the RoadTypeEntry hashable.
        """
        return hash(str(self.road_type))


@dataclass
class AvgSpeed:
    default_speed: float = 50.0
    speed_per_road_type: defaultdict[RoadTypeEntry, float] = field(
        default_factory=lambda: defaultdict(lambda: AvgSpeed.default_speed)
    )

    @property
    def road_types(self) -> list[RoadTypeEnum | list[RoadTypeEnum]]:
        return [_rte.road_type for _rte in self.speed_per_road_type.keys()]

    @staticmethod
    def _get_road_type_entry(
        road_type: str | RoadTypeEnum | list[RoadTypeEnum],
    ) -> RoadTypeEntry:
        if isinstance(road_type, str):
            if road_type.startswith("["):
                # If the roadtype is a str(list), convert it back to a list
                road_type = list(map(RoadTypeEnum.get_enum, literal_eval(road_type)))
            else:
                road_type = RoadTypeEnum.get_enum(road_type)
        return RoadTypeEntry(road_type)

    def get_avg_speed(
        self, road_type: str | RoadTypeEnum | list[RoadTypeEnum]
    ) -> float:
        return self.speed_per_road_type.get(
            self._get_road_type_entry(road_type), self.default_speed
        )

    def set_avg_speed(
        self, road_type: str | RoadTypeEnum | list[RoadTypeEnum], avg_speed: float
    ) -> None:
        self.speed_per_road_type[self._get_road_type_entry(road_type)] = round(
            avg_speed, 1
        )
