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
from typing import Type

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.adaptation_analysis_runner import AdaptationAnalysisRunner
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner
from ra2ce.runners.damages_analysis_runner import DamagesAnalysisRunner
from ra2ce.runners.losses_analysis_runner import LossesAnalysisRunner


class AnalysisRunnerFactory:
    @staticmethod
    def get_supported_runners(ra2ce_input: ConfigWrapper) -> list[Type[AnalysisRunner]]:
        """
        Gets the supported analysis runners for the given input.

        Args:
            ra2ce_input (Ra2ceInput): Input representing a set of network and analysis ini configurations.

        Returns:
            list[AnalysisRunner]: Supported runners for the given configuration.
        """
        if not ra2ce_input.analysis_config:
            return []
        _available_runners = [
            DamagesAnalysisRunner,
            LossesAnalysisRunner,
            AdaptationAnalysisRunner,
        ]
        _supported_runners = [
            _runner for _runner in _available_runners if _runner.can_run(ra2ce_input)
        ]
        if not _supported_runners:
            _err_mssg = "No analysis runner found for the given configuration."
            logging.error(_err_mssg)
            raise ValueError(_err_mssg)

        # Initialized selected supported runner (First one available).
        if len(_supported_runners) > 1:
            logging.warning(
                "More than one runner available, computation time could be longer than expected."
            )
        return _supported_runners

    @staticmethod
    def run(
        ra2ce_input: ConfigWrapper,
        analysis_collection: AnalysisCollection,
    ) -> list[AnalysisResultWrapper]:
        """
        Runs the given analysis collection.

        Args:
            ra2ce_input (Ra2ceInput): Input representing a set of network and analysis ini configurations.
            analysis_collection (AnalysisCollection): Collection of analyses to run.

        Returns:
            list[AnalysisResultWrapper]: List of analysis results.
        """
        _supported_runners = AnalysisRunnerFactory.get_supported_runners(ra2ce_input)
        _results = []
        for _runner_type in _supported_runners:
            _run_results = _runner_type().run(analysis_collection)
            _results.extend(_run_results)
        return _results
