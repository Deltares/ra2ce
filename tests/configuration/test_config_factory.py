from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.config_factory import ConfigFactory
from ra2ce.configuration.config_wrapper import ConfigWrapper
from tests import test_data


class TestConfigFactory:
    def test_get_config_wrapper_with_valid_input(self):
        # 1. Define test data.
        _test_dir = test_data / "simple_inputs"
        assert _test_dir.is_dir()
        _analysis_ini = _test_dir / "analysis.ini"
        _network_ini = _test_dir / "network.ini"

        assert _analysis_ini.is_file() and _network_ini.is_file()

        # 2. Run test.
        _input_config = ConfigFactory.get_config_wrapper(_network_ini, _analysis_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config, ConfigWrapper)
        assert isinstance(_input_config.analysis_config, AnalysisConfigBase)
        assert isinstance(_input_config.network_config, NetworkConfig)

    def test_from_input_paths_given_only_analysis(self):
        # 1. Define test data.
        _test_dir = test_data / "simple_inputs"
        assert _test_dir.is_dir()
        _analysis_ini = _test_dir / "analysis.ini"

        assert _analysis_ini.is_file()

        # 2. Run test.
        _input_config = ConfigFactory.get_config_wrapper(None, _analysis_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config, ConfigWrapper)
        assert isinstance(_input_config.analysis_config, AnalysisConfigBase)
        assert not _input_config.network_config

    def test_from_input_paths_given_only_network(self):
        # 1. Define test data.
        _test_dir = test_data / "simple_inputs"
        assert _test_dir.is_dir()
        _network_ini = _test_dir / "network.ini"

        assert _network_ini.is_file()

        # 2. Run test.
        _input_config = ConfigFactory.get_config_wrapper(_network_ini, None)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config, ConfigWrapper)
        assert isinstance(_input_config.network_config, NetworkConfig)
        assert not _input_config.analysis_config
