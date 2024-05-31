from pathlib import Path
from typing import Iterator

import pytest

from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.configuration.config_factory import ConfigFactory
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data


class TestConfigFactory:
    @pytest.fixture(name="simple_inputs")
    def _get_simple_inputs_acceptance_case(self) -> Iterator[tuple[Path, Path]]:
        _test_dir = test_data.joinpath("simple_inputs")
        assert _test_dir.is_dir()
        _analysis_ini = _test_dir / "analysis.ini"
        _network_ini = _test_dir / "network.ini"

        assert _analysis_ini.is_file() and _network_ini.is_file()

        yield (_network_ini, _analysis_ini)

    def test_get_config_wrapper_with_valid_input(
        self, simple_inputs: tuple[Path, Path]
    ):
        # 1. Define test data.
        _network_ini, _analysis_ini = simple_inputs

        # 2. Run test.
        _input_config = ConfigFactory.get_config_wrapper(_network_ini, _analysis_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config, ConfigWrapper)
        assert isinstance(_input_config.analysis_config, AnalysisConfigWrapper)
        assert isinstance(_input_config.network_config, NetworkConfigWrapper)
        assert isinstance(_input_config.network_config.config_data, NetworkConfigData)

    def test_from_input_paths_given_only_analysis(
        self, simple_inputs: tuple[Path, Path]
    ):
        # 1. Define test data.
        _, _analysis_ini = simple_inputs

        # 2. Run test.
        _input_config = ConfigFactory.get_config_wrapper(None, _analysis_ini)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config, ConfigWrapper)
        assert isinstance(_input_config.analysis_config, AnalysisConfigWrapper)
        assert not _input_config.network_config

    def test_from_input_paths_given_only_network(
        self, simple_inputs: tuple[Path, Path]
    ):
        # 1. Define test data.
        _network_ini, _ = simple_inputs

        # 2. Run test.
        _input_config = ConfigFactory.get_config_wrapper(_network_ini, None)

        # 3. Verify final expectations.
        assert _input_config
        assert isinstance(_input_config, ConfigWrapper)
        assert isinstance(_input_config.network_config, NetworkConfigWrapper)
        assert isinstance(_input_config.network_config.config_data, NetworkConfigData)
        assert not _input_config.analysis_config
