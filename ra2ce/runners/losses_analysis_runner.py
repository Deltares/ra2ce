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
from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.simple_analysis_runner_base import SimpleAnalysisRunnerBase


class LossesAnalysisRunner(SimpleAnalysisRunnerBase):
    def __str__(self) -> str:
        return "Losses Analysis Runner"

    @staticmethod
    def filter_supported_analyses(
        analysis_collection: AnalysisCollection,
    ) -> list[AnalysisLossesProtocol]:
        return analysis_collection.losses_analyses

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        if (
            not ra2ce_input.analysis_config
            or not ra2ce_input.analysis_config.config_data.losses_list
        ):
            return False
        return True
