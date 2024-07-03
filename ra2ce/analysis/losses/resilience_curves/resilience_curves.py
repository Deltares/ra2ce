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

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass(kw_only=True)
class ResilienceCurves:
    """
    Class to store the resilience curves for different link types.
    """

    resilience_curves: dict[
        tuple[RoadTypeEnum, tuple[float, float]], list[tuple[float, float]]
    ] = field(default_factory=dict)

    @property
    def ranges(self) -> list[tuple[float, float]]:
        return list(set(_key[1] for _key in self.resilience_curves.keys()))

    def has_resilience_curve(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> bool:
        """
        Check if a resilience curve exists for a given link type and hazard range.

        Args:
            link_type (RoadTypeEnum): The type of the link.
            hazard_range (tuple[float, float]): The range of the hazard.

        Returns:
            bool: True if the resilience curve exists.
        """
        return self.get_resilience_curve(link_type, hazard_range) is not None

    def get_resilience_curve(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> list[tuple[float, float]] | None:
        """
        Get the resilience curve for a given link type and hazard range.

        Args:
            link_type (RoadTypeEnum): The type of the link.
            hazard_range (tuple[float, float]): The range of the hazard.

        Returns:
            list[tuple[float, float]]: The resilience curve.
        """
        if (link_type, hazard_range) in self.resilience_curves.keys():
            return self.resilience_curves[(link_type, hazard_range)]
        return None

    def get_duration_steps(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> list[float]:
        """
        Get the duration steps for a given link type and hazard range.

        Args:
            link_type (RoadTypeEnum): The type of the link.
            hazard_range (tuple[float, float]): The range of the hazard.

        Returns:
            list[float]: The duration steps.
        """
        _curves = self.resilience_curves[(link_type, hazard_range)]
        return [curve[0] for curve in _curves]

    def get_functionality_loss_ratio(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> list[float]:
        """
        Get the functionality loss ratio for a given link type and hazard range.

        Args:
            link_type (RoadTypeEnum): The type of the link.
            hazard_range (tuple[float, float]): The range of the hazard.

        Returns:
            list[float]: The functionality loss ratio.
        """
        _curves = self.resilience_curves[(link_type, hazard_range)]
        return [curve[1] for curve in _curves]

    def calculate_disruption(
        self, link_type: RoadTypeEnum, hazard_range: tuple[float, float]
    ) -> float:
        """
        Calculate the disruption for a given link type and hazard range.
        It is guaranteed that the duration steps and functionality loss ratio have the same dimensions.

        Args:
            link_type (RoadTypeEnum): The type of the link.
            hazard_range (tuple[float, float]): The range of the hazard.

        Returns:
            float: The calculated disruption.
        """
        return sum(
            map(
                lambda x, y: x * y,
                self.get_duration_steps(link_type, hazard_range),
                self.get_functionality_loss_ratio(link_type, hazard_range),
            )
        )
