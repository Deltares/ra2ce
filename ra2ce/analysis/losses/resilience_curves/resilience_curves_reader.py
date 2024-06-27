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
import logging
from ast import literal_eval
from pathlib import Path
from re import findall

import pandas as pd

from ra2ce.analysis.losses.resilience_curves.resilience_curves import ResilienceCurves
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class ResilienceCurvesReader(FileReaderProtocol):
    def _parse_df(self, df: pd.DataFrame) -> ResilienceCurves:
        def parse_link_type_hazard_intensity(
            link_type_hazard_intensity: str,
        ) -> tuple[str, str, str]:
            return findall(r"^(\w+)_([\d.]+)-([\d.]+)$", link_type_hazard_intensity)[0]

        _link_type = []
        _hazard_range = []
        _duration_steps = []
        _functionality_loss_ratio = []

        for _, row in df.iterrows():
            _link_type_hazard_intensity = row["link_type_hazard_intensity"]
            _lt, _h_min, _h_max = parse_link_type_hazard_intensity(
                _link_type_hazard_intensity
            )
            _link_type.append(RoadTypeEnum.get_enum(_lt))
            _hazard_range.append((float(_h_min), float(_h_max)))
            _duration_steps.append(literal_eval(row["duration_steps"]))
            _functionality_loss_ratio.append(
                literal_eval(row["functionality_loss_ratio"])
            )

        if len(_duration_steps) != len(_functionality_loss_ratio):
            raise ValueError(
                "Duration steps and functionality loss ratio should have the same length"
            )

        return ResilienceCurves(
            link_type=_link_type,
            hazard_range=_hazard_range,
            duration_steps=_duration_steps,
            functionality_loss_ratio=_functionality_loss_ratio,
        )

    def read(self, file_path: Path | None) -> ResilienceCurves:
        if not file_path or not file_path.exists():
            logging.warning("No `csv` file found at %s.", file_path)
            return ResilienceCurves()

        _df = pd.read_csv(file_path, sep=";", on_bad_lines="skip")
        if "geometry" in _df.columns:
            raise ValueError(
                f"The csv file in {file_path} should not have a geometry column"
            )

        if not all(
            col in _df.columns
            for col in [
                "link_type_hazard_intensity",
                "duration_steps",
                "functionality_loss_ratio",
            ]
        ):
            raise ValueError(
                f"The csv file in {file_path} should have columns link_type_hazard_intensity, duration_steps, functionality_loss_ratio",
            )

        return self._parse_df(_df)
