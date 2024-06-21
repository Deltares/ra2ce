from pathlib import Path

import numpy

from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.avg_speed.avg_speed import AvgSpeed
from ra2ce.network.avg_speed.avg_speed_reader import AvgSpeedReader
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class TestAvgSpeedReader:
    def test_initialize(self):
        # 1. Execute test
        _reader = AvgSpeedReader()

        # 2. Verify expectations
        assert isinstance(_reader, AvgSpeedReader)
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_avg_speed(self, avg_speed_csv: Path):
        # 1. Define test data
        assert avg_speed_csv.is_file()
        _expected_values = [
            [[RoadTypeEnum.TERTIARY], 58.4],
            [[RoadTypeEnum.TERTIARY_LINK], 58.4],
            [[RoadTypeEnum.SECONDARY], 0.0],
            [[RoadTypeEnum.SECONDARY_LINK], 0.0],
            [[RoadTypeEnum.TRUNK], 0.0],
            [[RoadTypeEnum.TRUNK_LINK], 0.0],
            [[RoadTypeEnum.TERTIARY, RoadTypeEnum.SECONDARY], 60.0],
        ]

        # 2. Execute test
        _avg_speed = AvgSpeedReader().read(avg_speed_csv)

        # 3. Verify expectations
        assert isinstance(_avg_speed, AvgSpeed)
        for _expected_value in _expected_values:
            assert _avg_speed.get_avg_speed(_expected_value[0]) == _expected_value[1]
