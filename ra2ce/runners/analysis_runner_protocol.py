from typing import Protocol

from ra2ce.configuration.analysis_ini_configuration import AnalysisIniConfigurationBase
from ra2ce.ra2ce_input import Ra2ceInput


class AnalysisRunner(Protocol):
    @staticmethod
    def can_run(ra2ce_input: Ra2ceInput) -> bool:
        pass

    def run(self, analysis_config: AnalysisIniConfigurationBase) -> None:
        pass
