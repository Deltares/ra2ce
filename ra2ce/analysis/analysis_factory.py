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

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_direct_enum import (
    AnalysisDirectEnum,
)
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.direct.direct_damage import DirectDamage
from ra2ce.analysis.direct.effectiveness_measures import EffectivenessMeasure
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection


class AnalysisFactory:
    analysis: AnalysisSectionIndirect | AnalysisSectionDirect

    def __init__(
        self, analysis: AnalysisSectionIndirect | AnalysisSectionDirect
    ) -> None:
        self.analysis = analysis

    def get_analysis(self, graph_files: GraphFilesCollection) -> AnalysisProtocol:
        """
        Create an analysis based on the given analysis configuration and graph/network files.

        Args:
            graph_files (GraphFilesCollection): Collection of graph/network files.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisProtocol: The analysis to be executed.
        """
        if self.analysis.analysis == AnalysisDirectEnum.DIRECT:
            return DirectDamage(graph_files.base_network_hazard, self.analysis)
        elif self.analysis.analysis == AnalysisDirectEnum.EFFECTIVENESS_MEASURES:
            return EffectivenessMeasure(graph_files.base_network_hazard, self.analysis)
        elif True:
            pass
        raise NotImplementedError
