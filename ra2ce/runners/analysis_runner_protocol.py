from typing import Protocol

from ra2ce.configuration import AnalysisConfigBase
from ra2ce.configuration.config_wrapper import ConfigWrapper


class AnalysisRunner(Protocol):
    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        pass

    def run(self, analysis_config: AnalysisConfigBase) -> None:
        pass
