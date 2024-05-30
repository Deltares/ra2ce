from pathlib import Path

import pytest

from tests import acceptance_test_data


@pytest.fixture(name="valid_analysis_ini")
def valid_analysis_ini() -> Path:
    _ini_file = acceptance_test_data.joinpath("analyses.ini")
    assert _ini_file.exists()
    return _ini_file
