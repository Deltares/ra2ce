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

    def test_from_dict(self):
        _dict_values = {"the answer": 42}
        _config_data = AnalysisConfigDataWithNetwork.from_dict(_dict_values)

        assert isinstance(_config_data, AnalysisConfigDataWithNetwork)
        assert isinstance(_config_data, AnalysisConfigDataWithNetwork)
        assert _config_data == _dict_values


class TestAnalysisConfigDataWithoutNetwork:
    def test_initialize(self):
        _config_data = AnalysisConfigDataWithoutNetwork()
        assert isinstance(_config_data, AnalysisConfigDataWithoutNetwork)
        assert isinstance(_config_data, AnalysisConfigData)

    def test_from_dict(self):
        _dict_values = {"the answer": 42}
        _config_data = AnalysisConfigDataWithoutNetwork.from_dict(_dict_values)

        assert isinstance(_config_data, AnalysisConfigDataWithoutNetwork)
        assert isinstance(_config_data, AnalysisConfigDataWithoutNetwork)
        assert _config_data == _dict_values
