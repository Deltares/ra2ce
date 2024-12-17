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
from pathlib import Path

from pandas import DataFrame

from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.time_values.time_values import TimeValues


@dataclass
class TimeValuesReader(LossesInputDataReaderBase):
    """
    Class to read the time values from a csv file.
    """

    object_type: type = TimeValues
    csv_columns: list[str] = field(
        default_factory=lambda: ["trip_types", "value_of_time", "occupants"]
    )

    def _parse_df(self, df: DataFrame) -> TimeValues:
        _time_values = {
            TripPurposeEnum.get_enum(_trip_type): (_value_of_time, _occupants)
            for (_trip_type, _value_of_time, _occupants) in zip(
                df["trip_types"], df["value_of_time"], df["occupants"]
            )
        }

        return TimeValues(time_values=_time_values)

    def read(self, file_path: Path | None) -> TimeValues:
        return super().read(file_path)
