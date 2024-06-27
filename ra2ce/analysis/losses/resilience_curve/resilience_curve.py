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

import numpy as np

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass(kw_only=True)
class ResilienceCurve:
    link_type: list[RoadTypeEnum] = field(default_factory=list)
    hazard_range: list[tuple[float, float]] = field(default_factory=list)
    duration_steps: list[list[float]] = field(default_factory=list)
    functionality_loss_ratio: list[list[float]] = field(default_factory=list)

    @property
    def ranges(self) -> list[tuple[float, float]]:
        return list(set(self.hazard_range))

    def _get_index(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> int:
        _link_type_indices = np.where(np.array(self.link_type) == link_type)[0]
        _hazard_indices = np.where(np.array(self.hazard_range) == hazard_range)[0]
        return int(np.intersect1d(_link_type_indices, _hazard_indices)[0])

    def has_resilience_curve(self, link_type: RoadTypeEnum, hazard_min: float) -> bool:
        return self._get_index(link_type, hazard_min) != None

    def get_duration_steps(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> list[float]:
        return self.duration_steps[self._get_index(link_type, hazard_range)]

    def get_functionality_loss_ratio(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> list[float]:
        return self.functionality_loss_ratio[self._get_index(link_type, hazard_range)]

    def get_disruption(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> float:
        return sum(
            map(
                lambda x, y: x * y,
                self.get_duration_steps(link_type, hazard_range),
                self.get_functionality_loss_ratio(link_type, hazard_range),
            )
        )
