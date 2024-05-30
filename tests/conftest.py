from pathlib import Path

import pytest

from tests import acceptance_test_data


@pytest.fixture(name="valid_analysis_ini")
def _get_valid_analysis_ini_fixture() -> Path:
    _ini_file = acceptance_test_data.joinpath("analyses.ini")
    assert _ini_file.exists()
    return _ini_file
