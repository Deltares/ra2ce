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
from typing import Any

from pandas import DataFrame

from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.time_values.time_values import TimeValues


@dataclass
class TimeValuesReader(LossesInputDataReaderBase):
    csv_columns = ["trip_types", "value_of_time", "occupants"]
    data_type = type[TimeValues]

    def _parse_df(self, df: DataFrame) -> type[TimeValues]:
        _time_values = TimeValues()

        for _, row in df.iterrows():
            _time_values.trip_types.append(TripPurposeEnum.get_enum(row["trip_types"]))
            _time_values.value_of_time.append(int(row["value_of_time"]))
            _time_values.occupants.append(int(row["occupants"]))

        return _time_values
