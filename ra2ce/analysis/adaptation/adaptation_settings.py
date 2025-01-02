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
