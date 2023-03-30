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


from ra2ce.analyses.indirect import analyses_indirect
from ra2ce.configuration import AnalysisConfigBase
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class IndirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Indirect Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        return "indirect" in ra2ce_input.analysis_config.config_data

    def run(self, analysis_config: AnalysisConfigBase) -> None:
        analyses_indirect.IndirectAnalyses(
            analysis_config.config_data, analysis_config.graphs
        ).execute()
