from pathlib import Path
from typing import Any

import pytest

from ra2ce.analyses.analysis_config_data.readers.analysis_config_reader_with_network import (
    AnalysisConfigReaderWithNetwork,
)
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper


class TestAnalysisWithNetworkConfigReader:
    def test_init_without_network_data_raises(self):
        # 1. Run test.
        with pytest.raises(ValueError) as exc_err:
            AnalysisConfigReaderWithNetwork(None)

        # 2. Verify expectations.
        assert (
            str(exc_err.value)
            == "Network data mandatory for an AnalysisIniConfigurationReader reader."
        )

    @pytest.mark.parametrize(
        "ini_file",
        [
            pytest.param(None, id="None"),
            pytest.param("", id="Str"),
            pytest.param(Path("InvalidPath"), id="Non existent path dir."),
            pytest.param(Path("InvalidPath.ini"), id="Non existent path file."),
        ],
    )
    def test_read_without_ini_file_returns_none(self, ini_file: Any):
        # 1. Run test.
        with pytest.raises(ValueError) as exc_err:
            AnalysisConfigReaderWithNetwork(NetworkConfigWrapper()).read(ini_file)

        # 2. Verify expectations.
        assert str(exc_err.value) == "No analysis ini file 'Path' provided."
