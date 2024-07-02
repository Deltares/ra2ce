from pathlib import Path
from typing import Iterator

import pytest

from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from tests import test_data


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
