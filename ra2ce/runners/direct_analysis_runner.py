import logging

from ra2ce.analyses.direct import analyses_direct
from ra2ce.configuration import AnalysisConfigBase
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class DirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Direct Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        _network_config = ra2ce_input.network_config.config_data
        if "direct" not in ra2ce_input.analysis_config.config_data:
            return False
        if (
            "hazard" not in _network_config.keys()
            or "hazard_map" not in _network_config["hazard"].keys()
        ):
            logging.error(
                "Please define a hazardmap in your network.ini file. Unable to calculate direct damages."
            )
            return False
        return True

    def run(self, analysis_config: AnalysisConfigBase) -> None:
        analyses_direct.DirectAnalyses(
            analysis_config.config_data, analysis_config.graphs
        ).execute()
