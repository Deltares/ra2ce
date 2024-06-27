from pathlib import Path

from ra2ce.analysis.losses.resilience_curve.resilience_curve import ResilienceCurve
from ra2ce.analysis.losses.resilience_curve.resilience_curve_reader import (
    ResilienceCurveReader,
)
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class TestResilienceCurveReader:
    def test_initialize(self):
        # 1. Run test
        _reader = ResilienceCurveReader()

        # 2. Verify expections
        assert isinstance(_reader, ResilienceCurveReader)
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_resilience_curve(
        self,
        resilience_curve_csv: Path,
        resilience_curve_data: list[
            tuple[RoadTypeEnum, float, float, list[float], list[float]]
        ],
    ):
        # 1. Define test data
        assert resilience_curve_csv.is_file()

        # 2. Execute test
        _resilience_curve = ResilienceCurveReader().read(resilience_curve_csv)

        # 3. Verify expectations
        assert isinstance(_resilience_curve, ResilienceCurve)
        for _expected_value in resilience_curve_data:
            assert (
                _resilience_curve.get_duration_steps(
                    _expected_value[0], _expected_value[1]
                )
                == _expected_value[3]
            )
            assert (
                _resilience_curve.get_functionality_loss_ratio(
                    _expected_value[0], _expected_value[1]
                )
                == _expected_value[4]
            )
