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
class AccumulatedTaffic:
    regular: float = 1.0
    egalitarian: float = 1.0
    prioritarian: float = 1.0

    @classmethod
    def with_zeros(cls) -> AccumulatedTaffic:
        return cls(regular=0, egalitarian=0, prioritarian=0)

    def __add__(self, other: Union[AccumulatedTaffic, float, int]) -> AccumulatedTaffic:
        if isinstance(other, AccumulatedTaffic):
            return AccumulatedTaffic(
                regular=self.regular + other.regular,
                prioritarian=self.prioritarian + other.prioritarian,
                egalitarian=self.egalitarian + other.egalitarian,
            )
        elif isinstance(other, float) or isinstance(other, int):
            return AccumulatedTaffic(
                regular=self.regular + other,
                prioritarian=self.prioritarian + other,
                egalitarian=self.egalitarian + other,
            )
        else:
            raise NotImplementedError(
                "It is not possible to sum {} with a value of type {}.".format(
                    AccumulatedTaffic.__name__, type(other).__name__
                )
            )

    def __mul__(self, other: Union[AccumulatedTaffic, float, int]) -> AccumulatedTaffic:
        if isinstance(other, AccumulatedTaffic):
            return AccumulatedTaffic(
                regular=self.regular * other.regular,
                prioritarian=self.prioritarian * other.prioritarian,
                egalitarian=self.egalitarian * other.egalitarian,
            )
        elif isinstance(other, float) or isinstance(other, int):
            return AccumulatedTaffic(
                regular=self.regular * other,
                prioritarian=self.prioritarian * other,
                egalitarian=self.egalitarian * other,
            )
        else:
            raise NotImplementedError(
                "It is not possible to multiply {} with a value of type {}.".format(
                    AccumulatedTaffic.__name__, type(other).__name__
                )
            )
