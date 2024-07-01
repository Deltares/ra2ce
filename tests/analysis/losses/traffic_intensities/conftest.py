from pathlib import Path
from typing import Iterator

import pytest

from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from tests import test_data


@pytest.fixture(name="traffic_intensities_csv")
def get_traffic_intensities_csv_filepath() -> Iterator[Path]:
    _csv_file = test_data.joinpath(
        "losses", "csv_data_for_losses", "traffic_intensities.csv"
    )
    yield _csv_file


@pytest.fixture(name="traffic_intensities_data")
def get_traffic_intensities_data() -> Iterator[
    dict[tuple[TrafficPeriodEnum, TripPurposeEnum], list[int]]
]:
    """
    Get traffic intensities data for testing (links 1:5).

    Yields:
        Iterator[dict[tuple[PartOfDayEnum, RoadTypeEnum], list[int]]]: Traffic intensities data.
    """
    yield {
        (TrafficPeriodEnum.EVENING, TripPurposeEnum.FREIGHT): [0, 0, 0, 0, 0],
        (TrafficPeriodEnum.EVENING, TripPurposeEnum.COMMUTE): [10, 2, 8, 20, 4],
        (TrafficPeriodEnum.EVENING, TripPurposeEnum.BUSINESS): [20, 5, 7, 10, 8],
        (TrafficPeriodEnum.EVENING, TripPurposeEnum.OTHER): [0, 0, 0, 0, 0],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.FREIGHT): [0, 0, 0, 0, 0],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.COMMUTE): [10, 2, 8, 20, 4],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.BUSINESS): [20, 5, 7, 10, 8],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.OTHER): [0, 0, 0, 0, 0],
    }
