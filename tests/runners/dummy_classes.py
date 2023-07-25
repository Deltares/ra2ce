from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper


class DummyAnalysisConfig(AnalysisConfigWrapperBase):
    def __init__(self) -> None:
        self.config_data = {}


class DummyRa2ceInput(ConfigWrapper):
    def __init__(self) -> None:
        self.analysis_config = DummyAnalysisConfig()
        self.network_config = NetworkConfigWrapper()
