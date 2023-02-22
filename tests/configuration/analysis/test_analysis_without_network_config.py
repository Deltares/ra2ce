import pytest

from ra2ce.configuration.analysis.analysis_ini_config_data import AnalysisIniConfigData
from ra2ce.configuration.analysis.analysis_without_network_config import (
    AnalysisWithoutNetworkConfiguration,
)
from tests import acceptance_test_data


class TestAnalysisWithoutNetworkConfiguration:
    def test_init(self):
        _config = AnalysisWithoutNetworkConfiguration()
        assert isinstance(_config, AnalysisWithoutNetworkConfiguration)
        assert isinstance(_config.config_data, AnalysisIniConfigData)

    def test_given_no_ini_file_when_from_data_raises(self):
        with pytest.raises(FileNotFoundError):
            AnalysisWithoutNetworkConfiguration.from_data(
                acceptance_test_data / "non_existing_file.txt", None
            )

    def test_given_valid_file_when_is_valid_then_true(self):
        class MockedConfigData(AnalysisIniConfigData):
            def is_valid(self) -> bool:
                return True

        # 1. Define test data.
        _config = AnalysisWithoutNetworkConfiguration()
        _config.config_data = MockedConfigData()
        _config.ini_file = acceptance_test_data / "analyses.ini"
        assert _config.ini_file.exists()

        # 2. Run test and verify.
        assert _config.is_valid()

    def test_given_invalid_file_when_is_valid_then_false(self):
        class MockedConfigData(AnalysisIniConfigData):
            def is_valid(self) -> bool:
                return False

        # 1. Define test data.
        _config = AnalysisWithoutNetworkConfiguration()
        _config.config_data = MockedConfigData()
        _config.ini_file = acceptance_test_data / "not_a_file.ini"
        assert not _config.ini_file.exists()

        # 2. Run test and verify.
        assert not _config.is_valid()
