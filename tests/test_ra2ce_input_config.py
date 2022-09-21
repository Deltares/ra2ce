import pytest

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.ra2ce_input_config import Ra2ceInputConfig
from tests import test_data


class TestRa2ceInputConfig:
    def test_initialize(self):
        _input_config = Ra2ceInputConfig()
        assert _input_config
        assert not _input_config.analysis_config
        assert not _input_config.network_config

    def test_from_input_paths(self):
        # 1. Define test data.
        _test_dir = test_data / "simple_inputs"
        assert _test_dir.is_dir()
        _analysis_ini = _test_dir / "analysis.ini"
        _network_ini = _test_dir / "network.ini"

        assert _analysis_ini.is_file() and _network_ini.is_file()

        # 2. Run test.
        _input_config = Ra2ceInputConfig.from_input_paths(_analysis_ini, _network_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config.analysis_config, AnalysisConfigBase)
        assert isinstance(_input_config.network_config, NetworkConfig)
        assert _input_config.is_valid()

    @pytest.mark.skip(
        reason="Network Config does not seem to initialize files correctly."
    )
    def test_from_input_paths_given_only_analysis(self):
        # 1. Define test data.
        _test_dir = test_data / "simple_inputs"
        assert _test_dir.is_dir()
        _analysis_ini = _test_dir / "analysis.ini"

        assert _analysis_ini.is_file()

        # 2. Run test.
        _input_config = Ra2ceInputConfig.from_input_paths(_analysis_ini, None)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config.analysis_config, AnalysisConfigBase)
        assert not _input_config.network_config

    def test_from_input_paths_given_only_network(self):
        # 1. Define test data.
        _test_dir = test_data / "simple_inputs"
        assert _test_dir.is_dir()
        _network_ini = _test_dir / "network.ini"

        assert _network_ini.is_file()

        # 2. Run test.
        _input_config = Ra2ceInputConfig.from_input_paths(None, _network_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config.network_config, NetworkConfig)
        assert not _input_config.analysis_config
