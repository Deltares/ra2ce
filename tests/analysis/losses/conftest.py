from pathlib import Path
from typing import Iterator

import pytest

from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from tests import test_data


@pytest.fixture(name="resilience_curves_csv")
def get_resilience_curves_csv_filepath() -> Iterator[Path]:
    _csv_file = test_data.joinpath(
        "losses", "csv_data_for_losses", "resilience_curve.csv"
    )
    assert _csv_file.is_file()
    yield _csv_file


@pytest.fixture(name="resilience_curves_data")
def get_resilience_curves_data() -> Iterator[
    list[tuple[RoadTypeEnum, tuple[float, float], list[float], list[float]]]
]:
    """
    Get resilience curve data for testing.

    Yields:
        Iterator[list[tuple[RoadTypeEnum, tuple[float, float], list[float], list[float]]]]: list of resilience curve data.
    """
    yield [
        (RoadTypeEnum.MOTORWAY, (0.2, 0.5), [3.0, 5.0], [1.0, 0.4]),
        (RoadTypeEnum.MOTORWAY, (0.5, 1.2), [2.0, 4.0], [1.0, 0.3]),
    ]


@pytest.fixture(name="traffic_intensities_csv")
def get_traffic_intensities_csv_filepath() -> Iterator[Path]:
    _csv_file = test_data.joinpath(
        "losses", "csv_data_for_losses", "traffic_intensities.csv"
    )
    assert _csv_file.is_file()
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
        (TrafficPeriodEnum.EVENING_PEAK, TripPurposeEnum.FREIGHT): [0, 0, 0, 0, 0, 0],
        (TrafficPeriodEnum.EVENING_PEAK, TripPurposeEnum.COMMUTE): [10, 2, 8, 20, 4, 4],
        (TrafficPeriodEnum.EVENING_PEAK, TripPurposeEnum.BUSINESS): [20, 5, 7, 10, 8, 8],
        (TrafficPeriodEnum.EVENING_PEAK, TripPurposeEnum.OTHER): [0, 0, 0, 0, 0, 0],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.FREIGHT): [0, 0, 0, 0, 0, 0],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.COMMUTE): [10, 2, 8, 20, 4, 4],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.BUSINESS): [20, 5, 7, 10, 8, 8],
        (TrafficPeriodEnum.DAY, TripPurposeEnum.OTHER): [0, 0, 0, 0, 0, 0],
    }


@pytest.fixture(name="time_values_csv")
def get_time_values_csv_filepath() -> Iterator[Path]:
    _csv_file = test_data.joinpath(
        "losses", "csv_data_for_losses", "values_of_time.csv"
    )
    assert _csv_file.is_file()
    yield _csv_file


@pytest.fixture(name="time_values_data")
def get_time_values_data() -> Iterator[list[tuple[TripPurposeEnum, int, int]]]:
    """
    Get time values data for testing.

    Yields:
        Iterator[list[tuple[TripPurposeEnum, int, int]]]: Time values data.
    """
    yield [
        (TripPurposeEnum.BUSINESS, 5, 1),
        (TripPurposeEnum.COMMUTE, 10, 2),
        (TripPurposeEnum.FREIGHT, 0, 0),
        (TripPurposeEnum.OTHER, 0, 0),
    ]
