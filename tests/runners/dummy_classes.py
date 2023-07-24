from ra2ce.analyses.configuration import AnalysisConfigBase
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper
from ra2ce.configuration.config_wrapper import ConfigWrapper


class DummyAnalysisConfig(AnalysisConfigBase):
    def __init__(self) -> None:
        self.config_data = {}


class DummyRa2ceInput(ConfigWrapper):
    def __init__(self) -> None:
        self.analysis_config = DummyAnalysisConfig()
        self.network_config = NetworkConfigWrapper()
