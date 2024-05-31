from pathlib import Path
from typing import Iterator

import pytest

from tests import test_data


@pytest.fixture(name="graph_folder")
def _get_graph_test_folder_fixture() -> Iterator[Path]:
    yield test_data.joinpath("simple_inputs", "static", "output_graph")
