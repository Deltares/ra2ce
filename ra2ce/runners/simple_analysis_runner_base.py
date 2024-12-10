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
from abc import abstractmethod

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper_exporter import (
    AnalysisResultWrapperExporter,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class SimpleAnalysisRunnerBase(AnalysisRunner):
    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def filter_supported_analyses(
        analysis_collection: AnalysisCollection,
    ) -> list[AnalysisProtocol]:
        """
        Gets the supported analysis for a concrete runner.

        Args:
            analysis_collection (AnalysisCollection): Collection of analyses to filter.

        Returns:
            list[AnalysisProtocol]: Supported analyses from the provided collection.
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        raise NotImplementedError()

    def run(
        self, analysis_collection: AnalysisCollection
    ) -> list[AnalysisResultWrapper]:
        _results = []
        for analysis in self.filter_supported_analyses(analysis_collection):
            logging.info(
                "----------------------------- Started analyzing '%s'  -----------------------------",
                analysis.analysis.name,
            )
            starttime = time.time()

            _result_wrapper = analysis.execute()
            _results.append(_result_wrapper)
            AnalysisResultWrapperExporter().export_result(_result_wrapper)

            endtime = time.time()
            logging.info(
                "----------------------------- Analysis '%s' finished. "
                "Time: %ss  -----------------------------",
                analysis.analysis.name,
                str(round(endtime - starttime, 2)),
            )
        return _results
