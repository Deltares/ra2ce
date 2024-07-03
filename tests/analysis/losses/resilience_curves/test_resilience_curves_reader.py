from pathlib import Path

import pandas as pd
import pytest

from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.resilience_curves.resilience_curves import ResilienceCurves
from ra2ce.analysis.losses.resilience_curves.resilience_curves_reader import (
    ResilienceCurvesReader,
)
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class TestResilienceCurveReader:
    def test_initialize(self):
        # 1. Run test
        _reader = ResilienceCurvesReader()

        # 2. Verify expections
        assert isinstance(_reader, ResilienceCurvesReader)
        assert isinstance(_reader, LossesInputDataReaderBase)
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_resilience_curves(
        self,
        resilience_curves_csv: Path,
        resilience_curves_data: list[
            tuple[RoadTypeEnum, tuple[float, float], list[float], list[float]]
        ],
    ):
        # 1. Define test data
        assert resilience_curves_csv.is_file()

        # 2. Execute test
        _resilience_curves = ResilienceCurvesReader().read(resilience_curves_csv)

        # 3. Verify expectations
        assert isinstance(_resilience_curves, ResilienceCurves)
        for _expected_value in resilience_curves_data:
            _duration_steps = _resilience_curves.get_duration_steps(
                _expected_value[0], _expected_value[1]
            )
            assert len(_duration_steps) == len(_expected_value[2])
            assert all(_val in _expected_value[2] for _val in _duration_steps)

            _functionality_loss_ratio = _resilience_curves.get_functionality_loss_ratio(
                _expected_value[0], _expected_value[1]
            )
            assert len(_functionality_loss_ratio) == len(_expected_value[3])
            assert all(_val in _expected_value[3] for _val in _functionality_loss_ratio)

    def test__parse_df_mismatching_data_length(self):
        # 1. Define test data
        _resilience_curves_data = pd.DataFrame(
            {
                "link_type_hazard_intensity": ["motorway_0.1-0.2", "motorway_0.3-0.4"],
                "duration_steps": ["[1, 2]", "[1, 2, 3, 4]"],
                "functionality_loss_ratio": ["[0.1, 0.2]", "[0.1, 0.2, 0.3]"],
            }
        )

        # 2. Execute test
        with pytest.raises(ValueError) as exc_err:
            ResilienceCurvesReader()._parse_df(_resilience_curves_data)

        # 3. Verify expectations
        assert str(exc_err.value).startswith(
            "Duration steps and functionality loss ratio should have the same length"
        )
