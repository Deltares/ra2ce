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
import time

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper_exporter import (
    AnalysisResultWrapperExporter,
)
from ra2ce.analysis.damages.damages_result_wrapper import DamagesResultWrapper
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class DamagesAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Damages Analysis Runner"

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

    def run(self, analysis_config: AnalysisConfigWrapper) -> list[DamagesResultWrapper]:
        _analysis_collection = AnalysisCollection.from_config(analysis_config)
        _results = []
        for analysis in _analysis_collection.damages_analyses:
            logging.info(
                "----------------------------- Started analyzing '%s'  -----------------------------",
                analysis.analysis.name,
            )
            starttime = time.time()

            _result_wrapper = analysis.execute()
            AnalysisResultWrapperExporter().export_result(_result_wrapper)

            endtime = time.time()
            logging.info(
                "----------------------------- Analysis '%s' finished. "
                "Time: %ss  -----------------------------",
                analysis.analysis.name,
                str(round(endtime - starttime, 2)),
            )
        return _results
