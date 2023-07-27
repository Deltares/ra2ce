import pytest

from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_factory import (
    AnalysisConfigWrapperFactory,
)
from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisConfigDataWithNetwork,
    AnalysisConfigDataWithoutNetwork,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_with_network import (
    AnalysisConfigWrapperWithNetwork,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_without_network import (
    AnalysisConfigWrapperWithoutNetwork,
)
from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from tests import test_data


class TestAnalysisConfigFactory:
    def test_given_unknown_type_get_analysis_config_raises(self):
        class UnknownAnalysisIniConfigData(ConfigDataProtocol):
            pass

        # 1. Given test data
        _uknown_ini_config_data = UnknownAnalysisIniConfigData()
        assert isinstance(_uknown_ini_config_data, UnknownAnalysisIniConfigData)
        _a_path = test_data / "does_not_matter"
        _expected_error = (
            f"Analysis type {type(_uknown_ini_config_data)} not currently supported."
        )

        # 2. Run test
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisConfigWrapperFactory.get_analysis_config(
                _a_path, _uknown_ini_config_data, None
            )

        # 3. Verify expectations.
        assert str(exc_err.value) == _expected_error

    def test_given_known_with_network_config_get_analysis_config_returns_expected_value(
        self,
    ):
        # 1. Given test data.
        _ini_file_path = test_data / "simple_inputs" / "analysis.ini"
        _config_data = AnalysisConfigDataWithNetwork()
        _expected_type = AnalysisConfigWrapperWithNetwork
        assert isinstance(_config_data, AnalysisConfigData)

        # 2. Run test.
        _ini_config = AnalysisConfigWrapperFactory.get_analysis_config(
            _ini_file_path, _config_data, None
        )

        # 3. Verify expectations
        assert _ini_config
        assert isinstance(_ini_config, _expected_type)

    def test_given_known_without_network_config_get_analysis_config_returns_expected_value(
        self,
    ):
        # 1. Given test data.
        _ini_file_path = test_data / "simple_inputs" / "analysis.ini"
        _config_data = AnalysisConfigDataWithoutNetwork()

        _config_data["static"] = test_data / "simple_inputs" / "static"
        assert _config_data["static"].is_dir()

        _expected_type = AnalysisConfigWrapperWithoutNetwork
        assert isinstance(_config_data, AnalysisConfigData)

        # 2. Run test.
        _ini_config = AnalysisConfigWrapperFactory.get_analysis_config(
            _ini_file_path, _config_data, None
        )

        # 3. Verify expectations
        assert _ini_config
        assert isinstance(_ini_config, _expected_type)
