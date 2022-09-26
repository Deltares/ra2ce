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
