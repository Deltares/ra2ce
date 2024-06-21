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
from pathlib import Path

import pandas as pd

from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.avg_speed.avg_speed import AvgSpeed


class AvgSpeedReader(FileReaderProtocol):
    def read(self, file_path: Path) -> AvgSpeed:
        _avg_speed_data = pd.read_csv(file_path)
        _avg_speed = AvgSpeed()
        for _, row in _avg_speed_data.iterrows():
            _avg_speed.set_avg_speed(
                AvgSpeed.get_road_type_list(row["road_types"]), row["avg_speed"]
            )
        return _avg_speed
