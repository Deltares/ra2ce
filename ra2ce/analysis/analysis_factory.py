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
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.direct.direct_damage import DirectDamage
from ra2ce.analysis.direct.effectiveness_measures import EffectivenessMeasures
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.multi_link_isolated_locations import (
    MultiLinkIsolatedLocations,
)
from ra2ce.analysis.indirect.multi_link_origin_closest_destination import (
    MultiLinkOriginClosestDestination,
)
from ra2ce.analysis.indirect.multi_link_origin_destination import (
    MultiLinkOriginDestination,
)
from ra2ce.analysis.indirect.multi_link_redundancy import MultiLinkRedundancy
from ra2ce.analysis.indirect.optimal_route_origin_closest_destination import (
    OptimalRouteOriginClosestDestination,
)
from ra2ce.analysis.indirect.optimal_route_origin_destination import (
    OptimalRouteOriginDestination,
)
from ra2ce.analysis.indirect.losses import Losses
from ra2ce.analysis.indirect.single_link_redundancy import SingleLinkRedundancy
from ra2ce.network.hazard.hazard_names import HazardNames


class AnalysisFactory:

    @staticmethod
    def get_direct_analysis(
        analysis: AnalysisSectionDirect,
        analysis_config: AnalysisConfigWrapper,
    ) -> AnalysisDirectProtocol:
        """
        Create an analysis based on the given analysis configuration.

        Args:
            analysis (AnalysisSectionDirect): Analysis section.
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisDirectProtocol: The direct analysis to be executed.
        """
        _input_dict = dict(
            analysis=analysis,
            input_path=analysis_config.config_data.input_path,
            output_path=analysis_config.config_data.output_path,
        )
        if analysis.analysis == AnalysisDirectEnum.DIRECT:
            return DirectDamage(
                graph_file=analysis_config.graph_files.base_network_hazard,
                **_input_dict,
            )
        if analysis.analysis == AnalysisDirectEnum.EFFECTIVENESS_MEASURES:
            return EffectivenessMeasures(
                graph_file=analysis_config.graph_files.base_network_hazard,
                **_input_dict,
            )
        raise NotImplementedError(f"Analysis {analysis.analysis} not implemented")

    @staticmethod
    def get_indirect_analysis(
        analysis: AnalysisSectionIndirect,
        analysis_config: AnalysisConfigWrapper,
    ) -> AnalysisIndirectProtocol:
        """
        Create an analysis based on the given analysis configuration.

        Args:
            analysis (AnalysisSectionIndirect): Analysis section.
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisIndirectProtocol: The indirect analysis to be executed.
        """
        _input_dict = dict(
            analysis=analysis,
            input_path=analysis_config.config_data.input_path,
            static_path=analysis_config.config_data.static_path,
            output_path=analysis_config.config_data.output_path,
            hazard_names=HazardNames.from_config(analysis_config),
        )
        if analysis.analysis == AnalysisIndirectEnum.SINGLE_LINK_REDUNDANCY:
            return SingleLinkRedundancy(
                graph_file=analysis_config.graph_files.base_graph, **_input_dict
            )
        if analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_REDUNDANCY:
            return MultiLinkRedundancy(
                graph_file=analysis_config.graph_files.base_graph_hazard, **_input_dict
            )
        if analysis.analysis == AnalysisIndirectEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION:
            return OptimalRouteOriginDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph,
                **_input_dict,
                origins_destinations=analysis_config.config_data.origins_destinations,
            )
        if analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_ORIGIN_DESTINATION:
            return MultiLinkOriginDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph_hazard,
                **_input_dict,
                origins_destinations=analysis_config.config_data.origins_destinations,
            )
        if (
            analysis.analysis
            == AnalysisIndirectEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION
        ):
            return OptimalRouteOriginClosestDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph,
                **_input_dict,
                origins_destinations=analysis_config.config_data.origins_destinations,
                file_id=analysis_config.config_data.network.file_id,
            )
        if (
            analysis.analysis
            == AnalysisIndirectEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION
        ):
            return MultiLinkOriginClosestDestination(
                graph_file=analysis_config.graph_files.origins_destinations_graph,
                graph_file_hazard=analysis_config.graph_files.origins_destinations_graph_hazard,
                **_input_dict,
                origins_destinations=analysis_config.config_data.origins_destinations,
                file_id=analysis_config.config_data.network.file_id,
            )
        if analysis.analysis == AnalysisIndirectEnum.SINGLE_LINK_LOSSES:
            return Losses(
                network_config_data=analysis_config.config_data,
                graph_file=analysis_config.graph_files.base_graph_hazard,
                **_input_dict
            )
        if analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_LOSSES:
            return Losses(
                graph_file=analysis_config.graph_files.base_graph_hazard, **_input_dict
            )
        if analysis.analysis == AnalysisIndirectEnum.MULTI_LINK_ISOLATED_LOCATIONS:
            return MultiLinkIsolatedLocations(
                graph_file=analysis_config.graph_files.base_graph_hazard, **_input_dict
            )
        raise NotImplementedError(f"Analysis {analysis.analysis} not implemented")
