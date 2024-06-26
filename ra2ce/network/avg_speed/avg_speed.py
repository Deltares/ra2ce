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
    road_type: list[RoadTypeEnum]

    def __str__(self) -> str:
        """
        Override the str function to make it writeable as key in the CSV.
        """
        if len(self.road_type) == 1:
            return self.road_type[0].config_value
        return str([x.config_value for x in self.road_type])

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
    def road_types(self) -> list[list[RoadTypeEnum]]:
        return [_rte.road_type for _rte in self.speed_per_road_type.keys()]

    @staticmethod
    def get_road_type_list(
        road_type: str | list[str] | None,
    ) -> list[RoadTypeEnum] | None:
        if not road_type:
            return [RoadTypeEnum.INVALID]
        if isinstance(road_type, str):
            if road_type.startswith("["):
                # If the roadtype is a str(list), convert it back to a list
                return list(map(RoadTypeEnum.get_enum, literal_eval(road_type)))
            return [RoadTypeEnum.get_enum(road_type)]
        if isinstance(road_type, list):
            return list(map(RoadTypeEnum.get_enum, road_type))
        else:
            return [RoadTypeEnum.INVALID]

    def get_avg_speed(self, road_type: list[RoadTypeEnum]) -> float:
        return self.speed_per_road_type[RoadTypeEntry(road_type)]

    def set_avg_speed(self, road_type: list[RoadTypeEnum], avg_speed: float) -> None:
        self.speed_per_road_type[RoadTypeEntry(road_type)] = round(avg_speed, 1)
