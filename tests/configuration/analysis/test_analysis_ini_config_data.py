import pytest

from ra2ce.configuration.analysis.analysis_ini_config_data import (
    AnalysisIniConfigData,
    AnalysisWithNetworkIniConfigData,
    AnalysisWithoutNetworkIniConfigData,
)


class TestAnalysisIniConfigData:
    def test_initialize(self):
        _config_data = AnalysisIniConfigData()
        # At this moment it's not really mapped as a FOM.
        assert isinstance(_config_data, dict)
        assert isinstance(_config_data, AnalysisIniConfigData)

    def test_from_dict_raises_not_implemented_error(self):
        _expected_err = "Implement in concrete classes"
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisIniConfigData.from_dict({})
        assert str(exc_err.value) == _expected_err

    def test_is_valid_raises_not_implemented_error(self):
        _expected_err = "Implement in concrete classes"
        _ini_config_data = AnalysisIniConfigData()
        with pytest.raises(NotImplementedError) as exc_err:
            _ini_config_data.from_dict({})
        assert str(exc_err.value) == _expected_err


class TestAnalysisWithNetworkIniConfigData:
    def test_initialize(self):
        _config_data = AnalysisWithNetworkIniConfigData()
        assert isinstance(_config_data, AnalysisWithNetworkIniConfigData)
        assert isinstance(_config_data, AnalysisIniConfigData)

    def test_from_dict(self):
        _dict_values = {"the answer": 42}
        _config_data = AnalysisWithNetworkIniConfigData.from_dict(_dict_values)

        assert isinstance(_config_data, AnalysisWithNetworkIniConfigData)
        assert isinstance(_config_data, AnalysisWithNetworkIniConfigData)
        assert _config_data == _dict_values


class TestAnalysisWithoutNetworkIniConfigData:
    def test_initialize(self):
        _config_data = AnalysisWithoutNetworkIniConfigData()
        assert isinstance(_config_data, AnalysisWithoutNetworkIniConfigData)
        assert isinstance(_config_data, AnalysisIniConfigData)

    def test_from_dict(self):
        _dict_values = {"the answer": 42}
        _config_data = AnalysisWithoutNetworkIniConfigData.from_dict(_dict_values)

        assert isinstance(_config_data, AnalysisWithoutNetworkIniConfigData)
        assert isinstance(_config_data, AnalysisWithoutNetworkIniConfigData)
        assert _config_data == _dict_values
