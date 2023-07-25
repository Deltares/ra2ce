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

    def test_from_dict_raises_not_implemented_error(self):
        _expected_err = "Implement in concrete classes"
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisConfigData.from_dict({})
        assert str(exc_err.value) == _expected_err

    def test_is_valid_raises_not_implemented_error(self):
        _expected_err = "Implement in concrete classes"
        _ini_config_data = AnalysisConfigData()
        with pytest.raises(NotImplementedError) as exc_err:
            _ini_config_data.from_dict({})
        assert str(exc_err.value) == _expected_err


class TestAnalysisWithNetworkIniConfigData:
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


class TestAnalysisWithoutNetworkIniConfigData:
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
