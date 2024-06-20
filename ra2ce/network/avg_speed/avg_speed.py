from __future__ import annotations

from ast import literal_eval
from collections import defaultdict
from dataclasses import dataclass, field

import networkx as nx

import ra2ce.network.networks_utils as nut
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass
class RoadTypeEntry:
    road_type: RoadTypeEnum | list[RoadTypeEnum]

    def __hash__(self) -> int:
        return hash(str(self.road_type))

    def __str__(self) -> str:
        if isinstance(self.road_type, list):
            return str([x.config_value for x in self.road_type])
        return self.road_type.config_value


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
        self.speed_per_road_type[self._get_road_type_entry(road_type)] = avg_speed

    def set_avg_speed_time(self, original_graph: nx.Graph) -> nx.Graph:
        original_graph = nut.assign_avg_speed(original_graph, self, "highway")

        # make a time value of seconds, length of road streches is in meters
        for u, v, k, edata in original_graph.edges.data(keys=True):
            hours = (edata["length"] / 1000) / edata["avgspeed"]
            original_graph[u][v][k]["time"] = round(hours * 3600, 0)

        return original_graph
