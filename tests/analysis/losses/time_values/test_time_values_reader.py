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
        _times_values.get_occupants(TripPurposeEnum.BUSINESS)

        # 3. Verify expectations
        _trip_types, _value_of_time, _occupants = zip(*time_values_data)
        assert isinstance(_times_values, TimeValues)

        def check_data(data, reference_data) -> bool:
            return len(data) == len(reference_data) and all(
                _val in reference_data for _val in list(set(data))
            )

        assert check_data(_times_values.trip_types, _trip_types)
        assert check_data(_times_values.value_of_time, _value_of_time)
        assert check_data(_times_values.occupants, _occupants)
