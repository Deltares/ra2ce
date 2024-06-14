from dataclasses import dataclass, field

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass
class AvgSpeed:
    speed_dict: dict[RoadTypeEnum, float] = field(default_factory=dict)
