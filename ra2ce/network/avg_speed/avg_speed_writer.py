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

from ra2ce.common.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol
from ra2ce.network.avg_speed.avg_speed import AvgSpeed


class AvgSpeedWriter(Ra2ceExporterProtocol):
    def export(self, export_path: Path, export_data: AvgSpeed) -> None:
        export_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "road_types": list(map(str, export_data.speed_per_road_type.keys())),
                "avg_speed": export_data.speed_per_road_type.values(),
            }
        ).to_csv(export_path)
