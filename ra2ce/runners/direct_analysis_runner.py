import logging

from ra2ce.analyses.direct import analyses_direct
from ra2ce.configuration.analysis_ini_configuration import AnalysisIniConfigurationBase
from ra2ce.ra2ce_input_config import Ra2ceInputConfig
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class DirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Direct Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: Ra2ceInputConfig) -> bool:
        _network_config = ra2ce_input.network_config.config_data
        if not ("direct" in ra2ce_input.analysis_config.config_data):
            return False
        if not _network_config["hazard"]["hazard_map"]:
            logging.error(
                "Please define a hazardmap in your network.ini file. Unable to calculate direct damages."
            )
            return False
        return True

    def run(self, analysis_config: AnalysisIniConfigurationBase) -> None:
        analyses_direct.DirectAnalyses(
            analysis_config.config_data, analysis_config.graphs
        ).execute()
