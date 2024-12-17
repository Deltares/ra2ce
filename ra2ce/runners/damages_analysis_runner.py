"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.simple_analysis_runner_base import SimpleAnalysisRunnerBase


class DamagesAnalysisRunner(SimpleAnalysisRunnerBase):
    def __str__(self) -> str:
        return "Damages Analysis Runner"

    @staticmethod
    def filter_supported_analyses(
        analysis_collection: AnalysisCollection,
    ) -> list[AnalysisDamagesProtocol]:
        return analysis_collection.damages_analyses

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        if (
            not ra2ce_input.analysis_config
            or not ra2ce_input.analysis_config.config_data.damages_list
        ):
            return False
        if not ra2ce_input.network_config:
            return False
        _network_config = ra2ce_input.network_config.config_data
        if not _network_config.hazard or not _network_config.hazard.hazard_map:
            logging.error(
                "Please define a hazard map in your network.ini file. Unable to calculate damages."
            )
            return False
        return True
