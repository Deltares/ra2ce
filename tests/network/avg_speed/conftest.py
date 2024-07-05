from pathlib import Path
from typing import Iterator

import pytest

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from tests import test_data


@pytest.fixture(name="avg_speed_csv")
def get_avg_speed_csv_filepath() -> Iterator[Path]:
    _csv_file = test_data.joinpath("network", "test_read_avg_speed", "avg_speed.csv")
    yield _csv_file


@pytest.fixture(name="avg_speed_data")
def get_avg_speed_data() -> Iterator[list[tuple[list[RoadTypeEnum], float]]]:
    """
    Get average speed data for testing.

    Yields:
        Iterator[list[tuple[list[RoadTypeEnum], float]]]: list of road types and average speeds.
    """
    yield [
        ([RoadTypeEnum.TERTIARY], 1.2),
        ([RoadTypeEnum.TERTIARY_LINK], 2.3),
        ([RoadTypeEnum.SECONDARY], 3.4),
        ([RoadTypeEnum.SECONDARY_LINK], 4.5),
        ([RoadTypeEnum.TRUNK], 5.6),
        ([RoadTypeEnum.TRUNK_LINK], 6.7),
        ([RoadTypeEnum.TERTIARY, RoadTypeEnum.SECONDARY], 7.8),
    ]
