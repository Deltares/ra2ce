import logging
from ast import literal_eval
from pathlib import Path
from re import findall

import pandas as pd

from ra2ce.analysis.losses.resilience_curve.resilience_curve import ResilienceCurve
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class ResilienceCurveReader(FileReaderProtocol):
    def _parse_df(self, df: pd.DataFrame) -> ResilienceCurve:
        def parse_link_type_hazard_intensity(
            link_type_hazard_intensity: str,
        ) -> tuple[str, str, str]:
            return findall(r"^(\w+)_([\d.]+)-([\d.]+)$", link_type_hazard_intensity)[0]

        _link_type = []
        _hazard_min = []
        _hazard_max = []
        _duration_steps = []
        _functionality_loss_ratio = []

        for _, row in df.iterrows():
            _link_type_hazard_intensity = row["link_type_hazard_intensity"]
            _lt, _h_min, _h_max = parse_link_type_hazard_intensity(
                _link_type_hazard_intensity
            )
            _link_type.append(RoadTypeEnum.get_enum(_lt))
            _hazard_min.append(float(_h_min))
            _hazard_max.append(float(_h_max))
            _duration_steps.append(literal_eval(row["duration_steps"]))
            _functionality_loss_ratio.append(
                literal_eval(row["functionality_loss_ratio"])
            )

        if len(_duration_steps) != len(_functionality_loss_ratio):
            raise ValueError(
                "Duration steps and functionality loss ratio should have the same length"
            )

        return ResilienceCurve(
            link_type=_link_type,
            hazard_min=_hazard_min,
            hazard_max=_hazard_max,
            duration_steps=_duration_steps,
            functionality_loss_ratio=_functionality_loss_ratio,
        )

    def read(self, file_path: Path | None) -> ResilienceCurve:
        if not file_path or not file_path.exists():
            logging.warning("No `csv` file found at %s.", file_path)
            return ResilienceCurve()

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