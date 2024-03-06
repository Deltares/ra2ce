from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
)
from ra2ce.analysis.analysis_config_wrapper import (
    AnalysisConfigWrapper,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper


class DummyAnalysisConfigWrapper(AnalysisConfigWrapper):
    def __init__(self) -> None:
        self.config_data = AnalysisConfigData(analyses=[])

    @classmethod
    def from_data(cls, **kwargs):
        raise NotImplementedError()

    def configure(self) -> None:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()


class DummyRa2ceInput(ConfigWrapper):
    def __init__(self) -> None:
        self.analysis_config = DummyAnalysisConfigWrapper()
        self.network_config = NetworkConfigWrapper()
