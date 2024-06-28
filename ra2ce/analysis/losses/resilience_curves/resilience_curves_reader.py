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
from ast import literal_eval
from pathlib import Path
from re import findall

import pandas as pd

from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.resilience_curves.resilience_curves import ResilienceCurves
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class ResilienceCurvesReader(LossesInputDataReaderBase):
    csv_columns = [
        "link_type_hazard_intensity",
        "duration_steps",
        "functionality_loss_ratio",
    ]
    data_type = ResilienceCurves

    def _parse_df(self, df: pd.DataFrame) -> ResilienceCurves:
        def parse_link_type_hazard_intensity(
            link_type_hazard_intensity: str,
        ) -> tuple[str, str, str]:
            return findall(r"^(\w+)_([\d.]+)-([\d.]+)$", link_type_hazard_intensity)[0]

        _resilience_curves = ResilienceCurves()

        for _, row in df.iterrows():
            _link_type_hazard_intensity = row["link_type_hazard_intensity"]
            _lt, _h_min, _h_max = parse_link_type_hazard_intensity(
                _link_type_hazard_intensity
            )
            _resilience_curves.link_type.append(RoadTypeEnum.get_enum(_lt))
            _resilience_curves.hazard_range.append((float(_h_min), float(_h_max)))
            _resilience_curves.duration_steps.append(
                literal_eval(row["duration_steps"])
            )
            _resilience_curves.functionality_loss_ratio.append(
                literal_eval(row["functionality_loss_ratio"])
            )

        return _resilience_curves

    def read(self, file_path: Path | None) -> ResilienceCurves:
        return super().read(file_path)
