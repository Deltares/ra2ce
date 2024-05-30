from pathlib import Path
from typing import Any

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from tests import acceptance_test_data


class TestAnalysisConfigReader:
    def test_initialize(self):
        # 1. Run test.
        _reader = AnalysisConfigDataReader()

        # 2. Verify expectations.
        assert isinstance(_reader, AnalysisConfigDataReader)

    @pytest.mark.parametrize(
        "ini_file",
        [
            pytest.param(None, id="None"),
            pytest.param("", id="Str"),
            pytest.param(Path("InvalidPath"), id="Non existent path."),
            pytest.param(Path("InvalidPath.ini"), id="Non existent path file."),
        ],
    )
    def test_read_without_ini_file_raises_error(self, ini_file: Any):
        # 1. Run test.
        with pytest.raises(ValueError) as exc_err:
            AnalysisConfigDataReader().read(ini_file)

        # 2. Verify expectations.
        assert str(exc_err.value) == "No analysis ini file 'Path' provided."

    def test_read_succeeds(self):
        # 1. Define test data
        _ini_file = acceptance_test_data.joinpath("analyses.ini")
        _ini_file_output = acceptance_test_data.joinpath("output", "analyses.ini")
        if _ini_file_output.exists():
            _ini_file_output.unlink()

        # 2. Run test
        _config = AnalysisConfigDataReader().read(_ini_file)

        # 3. Verify expectations
        assert isinstance(_config.input_path, Path)
        assert _ini_file_output.exists()
