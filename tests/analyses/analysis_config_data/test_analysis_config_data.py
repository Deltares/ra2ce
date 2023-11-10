import pytest

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisConfigDataWithNetwork,
    AnalysisConfigDataWithoutNetwork,
)


class TestAnalysisConfigData:
    def test_initialize(self):
        _config_data = AnalysisConfigData()
        # At this moment it's not really mapped as a FOM.
        assert isinstance(_config_data, dict)
        assert isinstance(_config_data, AnalysisConfigData)


class TestAnalysisConfigDataWithNetwork:
    def test_initialize(self):
        _config_data = AnalysisConfigDataWithNetwork()
        assert isinstance(_config_data, AnalysisConfigDataWithNetwork)
        assert isinstance(_config_data, AnalysisConfigData)


class TestAnalysisConfigDataWithoutNetwork:
    def test_initialize(self):
        _config_data = AnalysisConfigDataWithoutNetwork()
        assert isinstance(_config_data, AnalysisConfigDataWithoutNetwork)
        assert isinstance(_config_data, AnalysisConfigData)
