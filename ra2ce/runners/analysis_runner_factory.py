import logging

from ra2ce.ra2ce_input import Ra2ceInput
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner
from ra2ce.runners.direct_analysis_runner import DirectAnalysisRunner
from ra2ce.runners.indirect_analysis_runner import IndirectAnalysisRunner


class AnalysisRunnerFactory:
    @staticmethod
    def get_runner(ra2ce_input: Ra2ceInput) -> AnalysisRunner:
        _available_runners = [DirectAnalysisRunner, IndirectAnalysisRunner]
        _supported_runners = [
            _runner for _runner in _available_runners if _runner.can_run(ra2ce_input)
        ]
        if not _supported_runners:
            logging.error("No analysis runner found for the given configuration.")

        if len(_supported_runners) > 1:
            logging.warn(
                f"More than one runner available, using {_supported_runners[0]}"
            )
        return _supported_runners[0]
