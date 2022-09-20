from typing import Protocol

from ra2ce.configuration.analysis_config_base import AnalysisConfigBase
from ra2ce.ra2ce_input_config import Ra2ceInputConfig


class AnalysisRunner(Protocol):
    @staticmethod
    def can_run(ra2ce_input: Ra2ceInputConfig) -> bool:
        pass

    def run(self, analysis_config: AnalysisConfigBase) -> None:
        pass
