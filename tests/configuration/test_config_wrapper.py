from pathlib import Path
from typing import Optional, Type

import pytest

from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_with_network import (
    AnalysisConfigWrapperWithNetwork,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_without_network import (
    AnalysisConfigWrapperWithoutNetwork,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper
from tests import test_data


class MockedAnalysisBase(AnalysisConfigWrapperBase):
    def configure(self) -> None:
        pass

    @classmethod
    def from_data(cls, **kwargs):
        pass


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
    @pytest.mark.parametrize(
        "analysis_wrapper",
        [
            pytest.param(
                AnalysisConfigWrapperWithNetwork, id="Analysis wrapper WITH network"
            ),
            pytest.param(
                AnalysisConfigWrapperWithoutNetwork,
                id="Analysis wrapper WITHOUT network",
            ),
        ],
    )
    def test_get_root_dir(
        self,
        network_ini: Optional[Path],
        analysis_ini: Optional[Path],
        analysis_wrapper: Type[AnalysisConfigWrapperBase],
    ):
        # 1. Define test data.
        _input_config = ConfigWrapper()
        _input_config.network_config = NetworkConfigWrapper()
        _input_config.analysis_config = analysis_wrapper()
        _input_config.network_config.ini_file = network_ini
        _input_config.analysis_config.ini_file = analysis_ini

        # 2. Run test.
        if not network_ini and not analysis_ini:
            with pytest.raises(ValueError):
                _input_config.root_dir
        else:
            _root_dir = _input_config.root_dir
            # 3. Verify expectations.
            assert _root_dir == test_data

    def test_is_valid_input_no_analysis_config(self):
        # 1. Define test data
        _input_config = ConfigWrapper()
        _input_config.network_config = NetworkConfigWrapper()
        _input_config.analysis_config = None

        # 2. Run test
        assert not _input_config.is_valid_input()

    def test_is_valid_input_given_invalid_network_config(self):
        class MockedAnalysis(MockedAnalysisBase):
            def is_valid(self) -> bool:
                return True

        class MockedNetwork(NetworkConfigWrapper):
            def is_valid(self) -> bool:
                return False

        # 1. Define test data.
        _wrapper = ConfigWrapper()
        _wrapper.network_config = MockedNetwork()
        _wrapper.analysis_config = MockedAnalysis()

        # 2. Run test.
        _result = _wrapper.is_valid_input()

        # 3. Verify final expectations.
        assert _result is False

    def test_is_valid_input_given_invalid_root_directories(self):
        class MockedAnalysis(MockedAnalysisBase):
            @property
            def root_dir(self) -> Path:
                return test_data / "a_path"

            def is_valid(self) -> bool:
                return True

        class MockedNetwork(NetworkConfigWrapper):
            @property
            def root_dir(self) -> Path:
                return test_data / "another_path"

            def is_valid(self) -> bool:
                return True

        # 1. Define test data.
        _wrapper = ConfigWrapper()
        _wrapper.network_config = MockedNetwork()
        _wrapper.analysis_config = MockedAnalysis()

        # 2. Run test.
        _result = _wrapper.is_valid_input()

        # 3. Verify final expectations.
        assert _result is False

    def test_is_valid_given_valid_analysis_no_network_config(self):
        class MockedAnalysis(MockedAnalysisBase):
            def is_valid(self) -> bool:
                return True

        # 1. Define test data.
        _wrapper = ConfigWrapper()
        _wrapper.analysis_config = MockedAnalysis()
        _wrapper.network_config = None

        # 2. Run test.
        _result = _wrapper.is_valid_input()

        # 3. Verify final expectations.
        assert _result is True

    def test_is_valid_given_valid_analysis_valid_network_config(self):
        class MockedAnalysis(MockedAnalysisBase):
            @property
            def root_dir(self) -> Path:
                return test_data

            def is_valid(self) -> bool:
                return True

        class MockedNetwork(NetworkConfigWrapper):
            @property
            def root_dir(self) -> Path:
                return test_data

            def is_valid(self) -> bool:
                return True

        # 1. Define test data.
        _wrapper = ConfigWrapper()
        _wrapper.analysis_config = MockedAnalysis()
        _wrapper.network_config = MockedNetwork()

        # 2. Run test.
        _result = _wrapper.is_valid_input()

        # 3. Verify final expectations.
        assert _result is True
