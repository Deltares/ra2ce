from pathlib import Path

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
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_resilience_curves(
        self,
        resilience_curves_csv: Path,
        resilience_curves_data: list[
            tuple[RoadTypeEnum, float, float, list[float], list[float]]
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