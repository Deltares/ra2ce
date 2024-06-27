from dataclasses import dataclass, field

import numpy as np

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass(kw_only=True)
class ResilienceCurve:
    link_type: list[RoadTypeEnum] = field(default_factory=list)
    hazard_min: list[float] = field(default_factory=list)
    hazard_max: list[float] = field(default_factory=list)
    duration_steps: list[list[float]] = field(default_factory=list)
    functionality_loss_ratio: list[list[float]] = field(default_factory=list)

    def _get_index(self, link_type: RoadTypeEnum, hazard_min: float) -> int:
        _link_type_indices = np.where(np.array(self.link_type) == link_type)[0]
        _hazard_min_indices = np.where(np.array(self.hazard_min) == hazard_min)[0]
        return int(np.intersect1d(_link_type_indices, _hazard_min_indices)[0])

    def get_duration_steps(
        self, link_type: RoadTypeEnum, hazard_min: float
    ) -> list[float]:
        return self.duration_steps[self._get_index(link_type, hazard_min)]

    def get_functionality_loss_ratio(
        self, link_type: RoadTypeEnum, hazard_min: float
    ) -> list[float]:
        return self.functionality_loss_ratio[self._get_index(link_type, hazard_min)]

    def get_disruption(self, link_type: RoadTypeEnum, hazard_min: float) -> float:
        return sum(
            map(
                lambda x, y: x * y,
                self.get_duration_steps(link_type, hazard_min),
                self.get_functionality_loss_ratio(link_type, hazard_min),
            )
        )
