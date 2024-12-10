from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.damages_analysis_runner import DamagesAnalysisRunner
from ra2ce.runners.simple_analysis_runner_base import SimpleAnalysisRunnerBase


class AdaptationAnalysisRunner(SimpleAnalysisRunnerBase):
    def __str__(self):
        return "Adaptation Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        if (
            not ra2ce_input.analysis_config
            or not ra2ce_input.analysis_config.config_data.adaptation
        ):
            return False
        return DamagesAnalysisRunner.can_run(ra2ce_input)

    @staticmethod
    def filter_supported_analyses(
        analysis_collection: AnalysisCollection,
    ) -> list[Adaptation]:
        return [analysis_collection.adaptation_analysis]
