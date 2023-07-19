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


@dataclass
class AccumulatedTaffic:
    regular: float = 1.0
    egalitarian: float = 1.0
    prioritarian: float = 1.0

    def __add__(self, other: AccumulatedTaffic) -> None:
        self.regular += other.regular
        self.prioritarian += other.prioritarian
        self.egalitarian += other.egalitarian

    def __mul__(self, other: AccumulatedTaffic) -> None:
        self.regular *= other.regular
        self.prioritarian *= other.prioritarian
        self.egalitarian *= other.egalitarian

    def product(self, value: float) -> None:
        """
        Multiplies all accumulated traffic properties with the provided `value`.

        Args:
            value (float): Value to multiply by.
        """
        self.regular *= value
        self.prioritarian *= value
        self.egalitarian *= value
