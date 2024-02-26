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

from dataclasses import dataclass
from typing import Union


@dataclass
class AccumulatedTraffic:
    utilitarian: float = 0.0
    egalitarian: float = 0.0
    prioritarian: float = 0.0

    def __add__(
        self, other: Union[AccumulatedTraffic, float, int]
    ) -> AccumulatedTraffic:
        """
        Overloading of the add (`operator.add` or simply `+`).
        This overload ensures we correctly add the `AccumulatedTraffic` attributes (`utilitarian`, `egalitarian`, `prioritarian`).
        """
        if isinstance(other, AccumulatedTraffic):
            return AccumulatedTraffic(
                utilitarian=self.utilitarian + other.utilitarian,
                prioritarian=self.prioritarian + other.prioritarian,
                egalitarian=self.egalitarian + other.egalitarian,
            )
        elif isinstance(other, float) or isinstance(other, int):
            return AccumulatedTraffic(
                utilitarian=self.utilitarian + other,
                prioritarian=self.prioritarian + other,
                egalitarian=self.egalitarian + other,
            )
        raise TypeError(
            "It is not possible to sum {} with a value of type {}.".format(
                AccumulatedTraffic.__name__, type(other).__name__
            )
        )

    def __mul__(
        self, other: Union[AccumulatedTraffic, float, int]
    ) -> AccumulatedTraffic:
        """
        Overloading of the multiply (`operator.mul` or simply `*`).
        This overload ensures we correctly multiply the `AccumulatedTraffic` attributes (`utilitarian`, `egalitarian`, `prioritarian`).
        """
        if isinstance(other, AccumulatedTraffic):
            return AccumulatedTraffic(
                utilitarian=self.utilitarian * other.utilitarian,
                prioritarian=self.prioritarian * other.prioritarian,
                egalitarian=self.egalitarian * other.egalitarian,
            )
        elif isinstance(other, float) or isinstance(other, int):
            return AccumulatedTraffic(
                utilitarian=self.utilitarian * other,
                prioritarian=self.prioritarian * other,
                egalitarian=self.egalitarian * other,
            )
        raise TypeError(
            "It is not possible to multiply {} with a value of type {}.".format(
                AccumulatedTraffic.__name__, type(other).__name__
            )
        )
