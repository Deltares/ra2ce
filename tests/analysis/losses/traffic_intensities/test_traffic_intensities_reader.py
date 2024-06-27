from pathlib import Path

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
        traffic_intensities_data: list[
            tuple[int, int, int, int, int, int, int, int, int, int, int]
        ],
    ):
        # 1. Define test data
        assert traffic_intensities_csv.is_file()

        # 2. Execute test
        _traffic_intensities = TrafficIntensitiesReader().read(traffic_intensities_csv)

        # 3. Verify expectations
        _field_names = [
            "link_id",
            "evening_total",
            "evening_freight",
            "evening_commute",
            "evening_business",
            "evening_other",
            "day_freight",
            "day_commute",
            "day_business",
            "day_other",
            "day_total",
        ]

        assert isinstance(_traffic_intensities, TrafficIntensities)
        _data = list(zip(*traffic_intensities_data))
        for i, _field_name in enumerate(_field_names):
            _values = _traffic_intensities.__getattribute__(_field_name)
            assert len(_values) == len(_data[i])
            assert all(_val in _data[i] for _val in _values)
