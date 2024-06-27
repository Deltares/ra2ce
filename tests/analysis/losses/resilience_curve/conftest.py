from pathlib import Path
from typing import Iterator

import pytest

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from tests import test_data


@pytest.fixture(name="resilience_curve_csv")
def get_resilience_curve_csv_filepath() -> Iterator[Path]:
    _csv_file = test_data.joinpath(
        "losses", "csv_data_for_losses", "resilience_curve.csv"
    )
    yield _csv_file


@pytest.fixture(name="resilience_curve_data")
def get_resilience_curve_data() -> Iterator[
    list[tuple[RoadTypeEnum, float, float, list[float], list[float]]]
]:
    """
    Get resilience curve data for testing.

    Yields:
        Iterator[list[tuple[RoadTypeEnum, float, float, list[float], list[float]]]]: list of resilience curve data.
    """
    yield [
        (RoadTypeEnum.MOTORWAY, 0.2, 0.5, [3.0, 5.0], [1.0, 0.4]),
        (RoadTypeEnum.MOTORWAY, 0.5, 1.2, [2.0, 4.0], [1.0, 0.3]),
    ]
