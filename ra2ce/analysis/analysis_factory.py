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
from ra2ce.analysis.direct import DirectDamage, EffectivenessMeasures
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
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
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.network.hazard.hazard_names import HazardNames


class AnalysisFactory:
    analysis: AnalysisSectionIndirect | AnalysisSectionDirect

    def __init__(
        self, analysis: AnalysisSectionIndirect | AnalysisSectionDirect
    ) -> None:
        self.analysis = analysis

    def get_direct_analysis(
        self, analysis_config: AnalysisConfigWrapper
    ) -> AnalysisDirectProtocol:
        """
        Create an analysis based on the given analysis configuration.

        Args:
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisIndirectProtocol: The direct analysis to be executed.
        """
        _input_dict = dict(
            analysis=self.analysis,
            input_path=analysis_config.config_data.input_path,
            output_path=analysis_config.config_data.output_path,
        )
        if self.analysis.analysis == AnalysisDirectEnum.DIRECT:
            return DirectDamage(
                graph_file=analysis_config.graph_files.base_network_hazard,
                **_input_dict,
            )
        if self.analysis.analysis == AnalysisDirectEnum.EFFECTIVENESS_MEASURES:
            return EffectivenessMeasures(
                graph_file=analysis_config.graph_files.base_network_hazard,
                **_input_dict,
            )
        raise NotImplementedError(f"Analysis {self.analysis.analysis} not implemented")

    def get_indirect_analysis(
        self, analysis_config: AnalysisConfigWrapper
    ) -> AnalysisIndirectProtocol:
        """
        Create an analysis based on the given analysis configuration.

        Args:
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisIndirectProtocol: The indirect analysis to be executed.
        """
        _input_dict = dict(
            analysis=self.analysis,
            input_path=analysis_config.config_data.input_path,
            output_path=analysis_config.config_data.output_path,
            hazard_names=HazardNames.from_config(analysis_config),
        )
        if self.analysis.analysis == AnalysisIndirectEnum.SINGLE_LINK_REDUNDANCY:
            return SingleLinkRedundancy(
                graph_file=analysis_config.graph_files.base_graph, **_input_dict
            )
        if self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_REDUNDANCY:
            return MultiLinkRedundancy(
                graph_file=analysis_config.graph_files.base_graph_hazard, **_input_dict
            )
        if (
            self.analysis.analysis
            == AnalysisIndirectEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION
        ):
            return OptimalRouteOriginDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph,
                **_input_dict,
            )
        if self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_ORIGIN_DESTINATION:
            return MultiLinkOriginDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph_hazard,
                **_input_dict,
            )
        if (
            self.analysis.analysis
            == AnalysisIndirectEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION
        ):
            return OptimalRouteOriginClosestDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph,
                **_input_dict,
            )
        if (
            self.analysis.analysis
            == AnalysisIndirectEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION
        ):
            return MultiLinkOriginClosestDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph,
                graph_file_hazard=analysis_config.graph_files.origins_destinations_graph_hazard,
                **_input_dict,
            )
        if self.analysis.analysis == AnalysisIndirectEnum.LOSSES:
            return Losses(analysis_config.graph_files.base_graph_hazard, **_input_dict)
        if self.analysis.analysis == AnalysisIndirectEnum.SINGLE_LINK_LOSSES:
            return SingleLinkLosses(
                graph_file=analysis_config.graph_files.base_graph_hazard, **_input_dict
            )
        if self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_LOSSES:
            return MultiLinkLosses(
                graph_file=analysis_config.graph_files.base_graph_hazard, **_input_dict
            )
        if self.analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_ISOLATED_LOCATIONS:
            return MultiLinkIsolatedLocations(
                graph_file=analysis_config.graph_files.base_graph_hazard, **_input_dict
            )
        raise NotImplementedError(f"Analysis {self.analysis.analysis} not implemented")
