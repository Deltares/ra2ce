from pathlib import Path

import pytest

from ra2ce.common.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol
from ra2ce.network.avg_speed.avg_speed import AvgSpeed
from ra2ce.network.avg_speed.avg_speed_writer import AvgSpeedWriter
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from tests import test_results


class TestAvgSpeedWriter:
    def test_initialize(self):
        # 1. Execute test
        _writer = AvgSpeedWriter()

        # 2. Verify expectations
        assert isinstance(_writer, AvgSpeedWriter)
        assert isinstance(_writer, Ra2ceExporterProtocol)

    def test_write_avg_speed(self, request: pytest.FixtureRequest):
        # 1. Define test data
        _avg_speed_csv = test_results.joinpath(request.node.name, "avg_speed.csv")
        _avg_speed_csv.unlink(missing_ok=True)
        assert not _avg_speed_csv.is_file()

        _avg_speed = AvgSpeed(
            speed_dict={
                RoadTypeEnum.TERTIARY: 1.0,
                RoadTypeEnum.TERTIARY_LINK: 2.1,
                RoadTypeEnum.SECONDARY: 3.2,
                RoadTypeEnum.SECONDARY_LINK: 4.3,
                RoadTypeEnum.TRUNK: 5.4,
                RoadTypeEnum.TRUNK_LINK: 6.5,
            }
        )

        # 2. Execute test
        AvgSpeedWriter().export(_avg_speed_csv, _avg_speed)

        # 3. Verify expectations
        assert _avg_speed_csv.is_file()
