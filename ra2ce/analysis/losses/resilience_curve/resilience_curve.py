from dataclasses import dataclass, field

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass(kw_only=True)
class ResilienceCurve:
    link_type: list[RoadTypeEnum] = field(default_factory=list)
    hazard_min: list[float] = field(default_factory=list)
    hazard_max: list[float] = field(default_factory=list)
    duration_steps: list[list[float]] = field(default_factory=list)
    functionality_loss_ratio: list[list[float]] = field(default_factory=list)

    @property
    def disruption(self) -> float:
        return sum(
            map(lambda x, y: x * y, self.duration_steps, self.functionality_loss_ratio)
        )
