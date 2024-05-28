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

from __future__ import annotations

from dataclasses import dataclass, field

from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol


@dataclass
class AnalysisCollection:
    direct_analyses: list[AnalysisDirectProtocol] = field(default_factory=list)
    indirect_analyses: list[AnalysisIndirectProtocol] = field(default_factory=list)

    @classmethod
    def from_config(cls, analysis_config: AnalysisConfigWrapper) -> AnalysisCollection:
        """
        Create an AnalysisCollection from an AnalysisConfigWrapper.

        Args:
            analysis_config (AnalysisConfigWrapper): The analysis configuration.

        Returns:
            AnalysisCollection: Collection of analyses to be executed.
        """
        return cls(
            direct_analyses=[
                AnalysisFactory.get_damages_analysis(analysis, analysis_config)
                for analysis in analysis_config.config_data.damages
            ],
            indirect_analyses=[
                AnalysisFactory.get_losses_analysis(analysis, analysis_config)
                for analysis in analysis_config.config_data.losses
            ],
        )
