from pathlib import Path
from typing import Iterator

import pytest

from tests import test_data


@pytest.fixture(name="avg_speed_csv")
def get_avg_speed_csv_filepath(request: pytest.FixtureRequest) -> Iterator[Path]:
    _ini_file = test_data.joinpath("network", request.node.name, "avg_speed.csv")
    yield _ini_file
