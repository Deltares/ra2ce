from pathlib import Path

import pytest

from ra2ce.configuration import AnalysisIniConfigData
from ra2ce.configuration.analysis.analysis_with_network_config import (
    AnalysisWithNetworkConfiguration,
)
from ra2ce.configuration.network.network_config import NetworkConfig
from tests import test_data


class TestAnalysisWithNetworkConfig:
    def test_from_data_no_file_raises(self):
        with pytest.raises(FileNotFoundError):
            AnalysisWithNetworkConfiguration.from_data(Path("not_a_file"), None)

    def test_initialize(self):
        _config = AnalysisWithNetworkConfiguration()
        assert isinstance(_config, AnalysisWithNetworkConfiguration)
        assert isinstance(_config.config_data, AnalysisIniConfigData)

    def test_from_data(self):
        # 1. Define test data.
        _ini_file = test_data / "acceptance_test_data" / "analyses.ini"
        assert _ini_file.exists()
        _config_data = AnalysisIniConfigData()

        # 2. Run test.
        _config = AnalysisWithNetworkConfiguration.from_data(_ini_file, _config_data)

        # 3. Verify final expectations.
        assert isinstance(_config, AnalysisWithNetworkConfiguration)
        assert _config.config_data == _config_data
        assert _config.ini_file == _ini_file

    def test_from_data_with_network(self):
        # 1. Define test data.
        _ini_file = test_data / "acceptance_test_data" / "analyses.ini"
        assert _ini_file.exists()
        _config_data = AnalysisIniConfigData()
        _network_config = NetworkConfig()

        # 2. Run test.
        _config = AnalysisWithNetworkConfiguration.from_data_with_network(
            _ini_file, _config_data, _network_config
        )

        # 3. Verify final expectations.
        assert isinstance(_config, AnalysisWithNetworkConfiguration)
        assert _config.config_data == _config_data
        assert _config.ini_file == _ini_file
        assert _config._network_config == _network_config

    def test_configure(self):
        # 1. Define test data.
        _ini_file = test_data / "acceptance_test_data" / "analyses.ini"
        assert _ini_file.exists()
        _config_data = AnalysisIniConfigData()
        _network_config = NetworkConfig()
        _config = AnalysisWithNetworkConfiguration.from_data_with_network(
            _ini_file, _config_data, _network_config
        )

        # 2. Run test.
        _config.configure()

    def test_is_valid(self):
        class DummyConfigData(AnalysisIniConfigData):
            def is_valid(self) -> bool:
                return True

        # 1. Define test data
        _ini_file = test_data / "acceptance_test_data" / "analyses.ini"
        assert _ini_file.exists()

        # 2. Run test.
        assert AnalysisWithNetworkConfiguration.from_data(
            _ini_file, DummyConfigData()
        ).is_valid()
