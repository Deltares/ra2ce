from pathlib import Path
from typing import Iterator

import pytest

from tests import test_data


@pytest.fixture(name="traffic_intensities_csv")
def get_traffic_intensities_csv_filepath() -> Iterator[Path]:
    _csv_file = test_data.joinpath(
        "losses", "csv_data_for_losses", "traffic_intensities.csv"
    )
    yield _csv_file


@pytest.fixture(name="traffic_intensities_data")
def get_traffic_intensities_data() -> Iterator[
    list[tuple[int, int, int, int, int, int, int, int, int, int, int]]
]:
    """
    Get traffic intensities data for testing.

    Yields:
        Iterator[list[tuple[int, int, int,int, int, int, int, int, int, int, int]]]: Traffic intensities data.
    """
    yield [
        (1, 0, 0, 10, 20, 0, 0, 10, 20, 0, 30),
        (2, 0, 0, 2, 5, 0, 0, 2, 5, 0, 7),
        (3, 0, 0, 8, 7, 0, 0, 8, 7, 0, 15),
        (4, 0, 0, 20, 10, 0, 0, 20, 10, 0, 30),
        (5, 0, 0, 4, 8, 0, 0, 4, 8, 0, 12),
    ]


@pytest.fixture(name="traffic_intensities_names")
def get_traffic_intensities_names() -> Iterator[list[str]]:
    """
    Get traffic intensities field names.

    Yields:
        Iterator[list[str]]: Traffic intensities field names.
    """
    yield [
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
