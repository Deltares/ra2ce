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

import pandas as pd

from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities import (
    TrafficIntensities,
)


@dataclass
class TrafficIntensitiesReader(LossesInputDataReaderBase):
    csv_columns = [
        "link_id",
        "evening_total",
        "evening_freight",
        "evening_commute",
        "evening_business",
        "evening_other",
        "day_freight",
        "day_commute",
        "day_business",
        "day_other",
        "day_total",
    ]
    separator = ","
    data_type = type[TrafficIntensities]

    def _parse_df(self, df: pd.DataFrame) -> TrafficIntensities:
        _traffic_intensities = TrafficIntensities()
        for _, row in df.iterrows():
            _traffic_intensities.link_id.append(row["link_id"])
            _traffic_intensities.evening_total.append(row["evening_total"])
            _traffic_intensities.evening_freight.append(row["evening_freight"])
            _traffic_intensities.evening_commute.append(row["evening_commute"])
            _traffic_intensities.evening_business.append(row["evening_business"])
            _traffic_intensities.evening_other.append(row["evening_other"])
            _traffic_intensities.day_freight.append(row["day_freight"])
            _traffic_intensities.day_commute.append(row["day_commute"])
            _traffic_intensities.day_business.append(row["day_business"])
            _traffic_intensities.day_other.append(row["day_other"])
            _traffic_intensities.day_total.append(row["day_total"])
        return _traffic_intensities
