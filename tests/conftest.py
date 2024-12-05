from pathlib import Path
from typing import Iterator

import pytest

from tests import acceptance_test_data, test_results


@pytest.fixture(name="valid_analysis_ini")
def _get_valid_analysis_ini_fixture() -> Iterator[Path]:
    _ini_file = acceptance_test_data.joinpath("analyses.ini")
    assert _ini_file.exists()
    yield _ini_file


@pytest.fixture(name="test_result_param_case")
def _get_test_result_param_case_path_builder(
    request: pytest.FixtureRequest,
) -> Iterator[Path]:
    _path_parts = (
        request.node.name.strip("[]").replace(" ", "_").replace("-", "_and_").split("[")
    )
    return test_results.joinpath(*_path_parts)
