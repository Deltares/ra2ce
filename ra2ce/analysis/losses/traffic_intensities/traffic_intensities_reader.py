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
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities import (
    TrafficIntensities,
)


@dataclass
class TrafficIntensitiesReader(LossesInputDataReaderBase):
    """
    Class to read the traffic intensities per traffic period from a csv file.
    """

    csv_columns: list[str] = field(default_factory=list)
    separator: str = ","
    object_type: type = TrafficIntensities

    def _parse_df(self, df: pd.DataFrame) -> TrafficIntensities:
        _traffic_intensities = TrafficIntensities()
        for col in df:
            if col == self.csv_columns[0]:
                _traffic_intensities.link_id = df[col].tolist()
                continue
            _col_parts = re.findall(r"(.+)_(\w+)", col)  # split on last underscore
            _traffic_period = TrafficPeriodEnum.get_enum(_col_parts[0][0])
            _trip_purpose = TripPurposeEnum.get_enum(_col_parts[0][1])
            _traffic_intensities.intensities[(_traffic_period, _trip_purpose)] = df[
                col
            ].tolist()
        return _traffic_intensities

    def read(self, file_path: Path | None) -> TrafficIntensities:
        return super().read(file_path)
