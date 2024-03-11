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
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import (
    AnalysisIndirectEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.direct import DirectDamage, EffectivenessMeasures
from ra2ce.analysis.indirect import (
    Losses,
    MultiLinkIsolatedLocations,
    MultiLinkLosses,
    MultiLinkOriginClosestDestination,
    MultiLinkOriginDestination,
    MultiLinkRedundancy,
    OptimalRouteOriginClosestDestination,
    OptimalRouteOriginDestination,
    SingleLinkLosses,
    SingleLinkRedundancy,
)


class AnalysisFactory:
    analysis: AnalysisSectionIndirect | AnalysisSectionDirect

    def __init__(
        self, analysis: AnalysisSectionIndirect | AnalysisSectionDirect
    ) -> None:
        self.analysis = analysis

    def get_analysis(self, analysis_config: AnalysisConfigWrapper) -> AnalysisProtocol:
        """
        Create an analysis based on the given analysis configuration.

        Args:
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisProtocol: The analysis to be executed.
        """
        if self.analysis.analysis == AnalysisDirectEnum.DIRECT:
            return DirectDamage(
                analysis_config.graph_files.base_network_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif self.analysis.analysis == AnalysisDirectEnum.EFFECTIVENESS_MEASURES:
            return EffectivenessMeasures(
                analysis_config.graph_files.base_network_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif self.analysis.analysis == AnalysisIndirectEnum.SINGLE_LINK_REDUNDANCY:
            return SingleLinkRedundancy(
                analysis_config.graph_files.base_graph,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_REDUNDANCY:
            return MultiLinkRedundancy(
                analysis_config.graph_files.base_graph_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif (
            self.analysis.analysis
            == AnalysisIndirectEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION
        ):
            return OptimalRouteOriginDestination(
                analysis_config.graph_files.origins_destinations_graph,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif (
            self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_ORIGIN_DESTINATION
        ):
            return MultiLinkOriginDestination(
                analysis_config.graph_files.origins_destinations_graph_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif (
            self.analysis.analysis
            == AnalysisIndirectEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION
        ):
            return OptimalRouteOriginClosestDestination(
                analysis_config.graph_files.origins_destinations_graph,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif (
            self.analysis.analysis
            == AnalysisIndirectEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION
        ):
            return MultiLinkOriginClosestDestination(
                analysis_config.graph_files.origins_destinations_graph,
                analysis_config.graph_files.origins_destinations_graph_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif self.analysis.analysis == AnalysisIndirectEnum.LOSSES:
            return Losses(
                analysis_config.graph_files.base_graph_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif self.analysis.analysis == AnalysisIndirectEnum.SINGLE_LINK_LOSSES:
            return SingleLinkLosses(
                analysis_config.graph_files.base_graph_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_LOSSES:
            return MultiLinkLosses(
                analysis_config.graph_files.base_graph_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        elif (
            self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_ISOLATED_LOCATIONS
        ):
            return MultiLinkIsolatedLocations(
                analysis_config.graph_files.base_graph_hazard,
                self.analysis,
                analysis_config.config_data.input_path,
                analysis_config.config_data.output_path,
            )
        raise NotImplementedError
