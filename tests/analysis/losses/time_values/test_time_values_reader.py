from pathlib import Path

from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)
from ra2ce.analysis.losses.time_values.time_values import TimeValues
from ra2ce.analysis.losses.time_values.time_values_reader import TimeValuesReader
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol


class TestTimeValuesReader:
    def test_initialize(self):
        # 1. Run test
        _reader = TimeValuesReader()

        # 2. Verify expections
        assert isinstance(_reader, TimeValuesReader)
        assert isinstance(_reader, LossesInputDataReaderBase)
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_time_values(
        self,
        time_values_csv: Path,
        time_values_data: list[tuple[TripPurposeEnum, int, int]],
    ):
        # 1. Define test data
        assert time_values_csv.is_file()

        # 2. Execute test
        _times_values = TimeValuesReader().read(time_values_csv)

        # 3. Verify expectations
        _trip_types, _value_of_time, _occupants = zip(*time_values_data)
        assert isinstance(_times_values, TimeValues)
        assert len(_times_values.trip_types) == len(_trip_types)
        assert all(_val in _trip_types for _val in _times_values.trip_types)
        assert len(_times_values.value_of_time) == len(_value_of_time)
        assert all(_val in _value_of_time for _val in _times_values.value_of_time)
        assert len(_times_values.occupants) == len(_occupants)
        assert all(_val in _occupants for _val in _times_values.occupants)
