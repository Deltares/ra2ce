from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.config_wrapper import ConfigWrapper


class DummyAnalysisConfig(AnalysisConfigBase):
    def __init__(self) -> None:
        self.config_data = {}

class DummyRa2ceInput(ConfigWrapper):
    def __init__(self) -> None:
        self.analysis_config = DummyAnalysisConfig()
        self.network_config = NetworkConfig()