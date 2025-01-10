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
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.runners.adaptation_analysis_runner import AdaptationAnalysisRunner
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner
from ra2ce.runners.damages_analysis_runner import DamagesAnalysisRunner
from ra2ce.runners.losses_analysis_runner import LossesAnalysisRunner


class AnalysisRunnerFactory:
    @staticmethod
    def get_supported_runners(
        analysis_collection: AnalysisCollection,
    ) -> list[AnalysisRunner]:
        """
        Gets the supported analysis runners for the given input.

        Args:
            analysis_collection (AnalysisCollection): Collection of analyses to run.

        Returns:
            list[AnalysisRunner]: Supported runners for the given configuration.
        """
        if not analysis_collection:
            return []
        _available_runners: list[AnalysisRunner] = [
            DamagesAnalysisRunner(),
            LossesAnalysisRunner(),
            AdaptationAnalysisRunner(),
        ]
        _supported_runners = []
        for _analysis in analysis_collection.analyses:
            _supported_runner = [
                _runner
                for _runner in _available_runners
                if _runner.can_run(_analysis, analysis_collection)
            ]
            if not _supported_runner:
                _err_mssg = "No analysis runner found for the given configuration."
                logging.error(_err_mssg)
                raise ValueError(_err_mssg)
            _supported_runners.append(_supported_runner[0])

        return list(set(_supported_runners))

    @staticmethod
    def run(
        analysis_collection: AnalysisCollection,
    ) -> list[AnalysisResultWrapper]:
        """
        Runs the given analysis collection.

        Args:
            analysis_collection (AnalysisCollection): Collection of analyses to run.

        Returns:
            list[AnalysisResultWrapper]: List of analysis results.
        """
        _supported_runners = AnalysisRunnerFactory.get_supported_runners(
            analysis_collection
        )
        _results = []
        for _runner in _supported_runners:
            _run_results = _runner.run(analysis_collection)
            _results.extend(_run_results)
        return _results
