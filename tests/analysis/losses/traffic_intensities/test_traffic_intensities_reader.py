from pathlib import Path

from ra2ce.analysis.analysis_config_data.enums.part_of_day_enum import PartOfDayEnum
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
        _reader = TrafficIntensitiesReader()

        # 2. Verify expections
        assert isinstance(_reader, TrafficIntensitiesReader)
        assert isinstance(_reader, LossesInputDataReaderBase)
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_traffic_intensities(
        self,
        traffic_intensities_csv: Path,
        traffic_intensities_data: dict[
            tuple[PartOfDayEnum, TripPurposeEnum], list[int]
        ],
    ):
        # 1. Define test data
        assert traffic_intensities_csv.is_file()

        # 2. Execute test
        _traffic_intensities = TrafficIntensitiesReader().read(traffic_intensities_csv)

        # 3. Verify expectations
        assert isinstance(_traffic_intensities, TrafficIntensities)
        for _key in traffic_intensities_data:
            assert _key in _traffic_intensities.intensities
            assert (
                traffic_intensities_data[_key] == _traffic_intensities.intensities[_key]
            )