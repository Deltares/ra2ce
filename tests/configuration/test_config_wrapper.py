from pathlib import Path
from typing import Optional

import pytest

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.config_wrapper import ConfigWrapper
from tests import test_data


class TestConfigWrapper:
    def test_initialize(self):
        _input_config = ConfigWrapper()
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
        _input_config = ConfigWrapper.from_input_paths(_analysis_ini, _network_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config.analysis_config, AnalysisConfigBase)
        assert isinstance(_input_config.network_config, NetworkConfig)

    def test_from_input_paths_given_only_analysis(self):
        # 1. Define test data.
        _test_dir = test_data / "simple_inputs"
        assert _test_dir.is_dir()
        _analysis_ini = _test_dir / "analysis.ini"

        assert _analysis_ini.is_file()

        # 2. Run test.
        _input_config = ConfigWrapper.from_input_paths(_analysis_ini, None)

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
        _input_config = ConfigWrapper.from_input_paths(None, _network_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config.network_config, NetworkConfig)
        assert not _input_config.analysis_config

    @pytest.mark.parametrize(
        "network_ini",
        [
            pytest.param(
                test_data / "simple_inputs" / "network.ini", id="Valid network ini."
            ),
            pytest.param(None, id="No INI network."),
        ],
    )
    @pytest.mark.parametrize(
        "analysis_ini",
        [
            pytest.param(
                test_data / "simple_inputs" / "analysis.ini", id="Valid analysis ini."
            ),
            pytest.param(None, id="No INI analysis."),
        ],
    )
    def test_get_root_dir(
        self, network_ini: Optional[Path], analysis_ini: Optional[Path]
    ):
        # 1. Define test data.
        _input_config = ConfigWrapper()
        _input_config.network_config = NetworkConfig()
        _input_config.analysis_config = AnalysisConfigBase()
        _input_config.network_config.ini_file = network_ini
        _input_config.analysis_config.ini_file = analysis_ini

        # 2. Run test.
        if not network_ini and not analysis_ini:
            with pytest.raises(ValueError):
                _input_config.get_root_dir()
        else:
            _root_dir = _input_config.get_root_dir()
            # 3. Verify expectations.
            assert _root_dir == test_data

    def test_is_valid_input_no_analysis_config(self):
        # 1. Define test data
        _input_config = ConfigWrapper()
        _input_config.network_config = NetworkConfig()
        _input_config.analysis_config = None

        # 2. Run test
        assert not _input_config.is_valid_input()
