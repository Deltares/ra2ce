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
from dataclasses import dataclass

import numpy as np


@dataclass
class AdaptationSettings:
    discount_rate: float = 0.0
    time_horizon: float = 0.0
    climate_factor: float = 0.0
    initial_frequency: float = 0.0

    @property
    def net_present_value_factor(self) -> float:
        """
        Calculate the net present value factor for the entire time horizon.
        To be multiplied to the event impact to obtain the net present value.
        """
        _years_array = np.arange(0, self.time_horizon)
        _frequency_per_year = (
            self.initial_frequency + _years_array * self.climate_factor
        )
        _discount = (1 + self.discount_rate) ** _years_array
        _ratio = _frequency_per_year / _discount
        return _ratio.sum()
