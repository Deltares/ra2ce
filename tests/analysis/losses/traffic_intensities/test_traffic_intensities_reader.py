from pathlib import Path

from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities import (
    TrafficIntensities,
)
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities_reader import (
    TrafficIntensitiesReader,
)
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol


class TestTimeValuesReader:
    def test_initialize(self):
        # 1. Run test
        _reader = TrafficIntensitiesReader("link_id")

        # 2. Verify expections
        assert isinstance(_reader, TrafficIntensitiesReader)
        assert isinstance(_reader, LossesInputDataReaderBase)
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_traffic_intensities(
        self,
        traffic_intensities_csv: Path,
        traffic_intensities_data: dict[
            tuple[TrafficPeriodEnum, TripPurposeEnum], list[int]
        ],
    ):
        # 1. Define test data
        assert traffic_intensities_csv.is_file()

        # 2. Execute test
        _traffic_intensities = TrafficIntensitiesReader("link_id").read(
            traffic_intensities_csv
        )

        # 3. Verify expectations
        assert isinstance(_traffic_intensities, TrafficIntensities)
        for _traffic_key, _traffic_data_reference in traffic_intensities_data.items():
            assert _traffic_key in _traffic_intensities.intensities
            assert (
                _traffic_data_reference
                == _traffic_intensities.intensities[_traffic_key]
            )
