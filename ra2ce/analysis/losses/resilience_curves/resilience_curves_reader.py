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
from dataclasses import dataclass, field
from pathlib import Path
from re import findall

import pandas as pd

from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.resilience_curves.resilience_curves import ResilienceCurves
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


@dataclass
class ResilienceCurvesReader(LossesInputDataReaderBase):
    """
    Class to read the resilience curves from a csv file.
    """

    object_type: type = ResilienceCurves
    csv_columns: list[str] = field(
        default_factory=lambda: [
            "link_type_hazard_intensity",
            "duration_steps",
            "functionality_loss_ratio",
        ]
    )

    def _parse_df(self, df: pd.DataFrame) -> ResilienceCurves:
        def parse_link_type_hazard_intensity(
            link_type_hazard_intensity: str,
        ) -> tuple[str, str, str]:
            return findall(r"^(\w+)_([\d.]+)-([\d.]+)$", link_type_hazard_intensity)[0]

        _resilience_curves = {}
        for _, row in df.iterrows():
            _link_type_hazard_intensity = row["link_type_hazard_intensity"]
            _lt, _h_min, _h_max = parse_link_type_hazard_intensity(
                _link_type_hazard_intensity
            )
            _ds_list = literal_eval(row["duration_steps"])
            _flr_list = literal_eval(row["functionality_loss_ratio"])
            if len(_ds_list) != len(_flr_list):
                raise ValueError(
                    f"Duration steps and functionality loss ratio should have the same length ({_link_type_hazard_intensity})."
                )
            _resilience_curves[
                (RoadTypeEnum.get_enum(_lt), (float(_h_min), float(_h_max)))
            ] = [(float(_ds), float(_flr)) for _ds, _flr in zip(_ds_list, _flr_list)]

        return ResilienceCurves(resilience_curves=_resilience_curves)

    def read(self, file_path: Path | None) -> ResilienceCurves:
        return super().read(file_path)
