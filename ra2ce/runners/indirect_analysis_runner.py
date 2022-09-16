from ra2ce.ra2ce_input import Ra2ceInput
from ra2ce.configuration.analysis_ini_configuration import AnalysisIniConfigurationBase
from ra2ce.analyses.indirect import analyses_indirect
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class IndirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Indirect Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: Ra2ceInput) -> bool:
        return super().can_run(ra2ce_input)

    def run(self, analysis_config: AnalysisIniConfigurationBase) -> None:
        analyses_indirect.IndirectAnalyses(
            analysis_config.config_data, analysis_config.graphs
        ).execute()
