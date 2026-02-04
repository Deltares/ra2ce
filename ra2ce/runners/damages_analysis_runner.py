"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023-2026 Stichting Deltares

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

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.runners.simple_analysis_runner_base import SimpleAnalysisRunnerBase


class DamagesAnalysisRunner(SimpleAnalysisRunnerBase):
    def __str__(self) -> str:
        return "Damages Analysis Runner"

    @staticmethod
    def filter_supported_analyses(
        analysis_collection: AnalysisCollection,
    ) -> list[AnalysisDamagesProtocol]:
        return analysis_collection.damages_analyses

    def can_run(
        self, analysis: AnalysisProtocol, analysis_collection: AnalysisCollection
    ) -> bool:
        if not super().can_run(analysis, analysis_collection):
            return False
        _graph = analysis_collection.damages_analyses[0].graph_file_hazard.get_graph()
        if not isinstance(_graph, GeoDataFrame):
            logging.error(
                "Please define a hazard map in your network.ini file. Unable to calculate damages."
            )
            return False
        return True
