from dataclasses import dataclass
from pathlib import Path

from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data


class MockedAnalysisConfigWrapper(AnalysisConfigWrapper):
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

    def test_is_valid_input_no_analysis_config(self):
        # 1. Define test data
        _input_config = ConfigWrapper()
        _input_config.network_config = NetworkConfigWrapper()
        _input_config.analysis_config = None

        # 2. Run test
        assert not _input_config.is_valid_input()

    def test_is_valid_input_given_invalid_network_config(self):
        class MockedAnalysis(MockedAnalysisConfigWrapper):
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
        @dataclass
        class MockedAnalysisConfig(ConfigDataProtocol):
            _root_path: Path

        class MockedAnalysis(MockedAnalysisConfigWrapper):
            def __init__(self) -> None:
                self.config_data = MockedAnalysisConfig(_root_path=test_data / "a_path")

            def is_valid(self) -> bool:
                return True

        @dataclass
        class MockedAnalysisNetworkConfig(ConfigDataProtocol):
            root_path: Path

        class MockedNetwork(NetworkConfigWrapper):
            def __init__(self) -> None:
                self.config_data = MockedAnalysisNetworkConfig(
                    root_path=test_data / "another_path"
                )

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
        class MockedAnalysis(MockedAnalysisConfigWrapper):
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
        @dataclass
        class MockedAnalysisConfig(ConfigDataProtocol):
            _root_path: Path

        class MockedAnalysis(MockedAnalysisConfigWrapper):
            def __init__(self) -> None:
                self.config_data = MockedAnalysisConfig(_root_path=test_data)

            def is_valid(self) -> bool:
                return True

        @dataclass
        class MockedNetworkConfig(ConfigDataProtocol):
            root_path: Path

        class MockedNetwork(NetworkConfigWrapper):
            def __init__(self) -> None:
                self.config_data = MockedNetworkConfig(root_path=test_data)

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
