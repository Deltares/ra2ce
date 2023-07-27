from pathlib import Path
from typing import Any
from ra2ce.analyses.analysis_config_data.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.analyses.analysis_config_data.readers.analysis_config_reader_without_network import (
    AnalysisConfigReaderWithoutNetwork,
)

import pytest


class TestAnalysisWithoutNetworkConfigReader:
    def test_initialize(self):
        # 1. Run test.
        _reader = AnalysisConfigReaderWithoutNetwork()

        # 2. Verify expectations.
        assert isinstance(_reader, AnalysisConfigReaderWithoutNetwork)
        assert isinstance(_reader, AnalysisConfigReaderBase)

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
            AnalysisConfigReaderWithoutNetwork().read(ini_file)

        # 2. Verify expectations.
        assert str(exc_err.value) == "No analysis ini file 'Path' provided."
