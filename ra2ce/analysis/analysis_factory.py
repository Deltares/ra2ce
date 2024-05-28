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
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.direct.direct_damage import DirectDamage
from ra2ce.analysis.direct.effectiveness_measures import EffectivenessMeasures
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.losses import Losses
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
from ra2ce.analysis.indirect.single_link_redundancy import SingleLinkRedundancy


class AnalysisFactory:
    @staticmethod
    def get_damages_analysis(
        analysis: AnalysisSectionDamages,
        analysis_config: AnalysisConfigWrapper,
    ) -> AnalysisDirectProtocol:
        """
        Create an analysis based on the given analysis configuration.

        Args:
            analysis (AnalysisSectionDamages): Analysis section.
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisDirectProtocol: The direct analysis to be executed.
        """
        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=analysis,
            analysis_config=analysis_config,
            graph_file_hazard=analysis_config.graph_files.base_network_hazard,
        )
        if analysis.analysis == AnalysisDamagesEnum.DIRECT_DAMAGE:
            return DirectDamage(_analysis_input)
        if analysis.analysis == AnalysisDamagesEnum.EFFECTIVENESS_MEASURES:
            return EffectivenessMeasures(_analysis_input)
        raise NotImplementedError(f"Analysis {analysis.analysis} not implemented")

    @staticmethod
    def get_losses_analysis(
        analysis: AnalysisSectionLosses,
        analysis_config: AnalysisConfigWrapper,
    ) -> AnalysisIndirectProtocol:
        """
        Create an analysis based on the given analysis configuration.

        Args:
            analysis (AnalysisSectionLosses): Analysis section.
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            AnalysisIndirectProtocol: The indirect analysis to be executed.
        """
        if analysis.analysis == AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY:
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file=analysis_config.graph_files.base_graph,
            )
            return SingleLinkRedundancy(_analysis_input)
        if analysis.analysis == AnalysisLossesEnum.MULTI_LINK_REDUNDANCY:
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file_hazard=analysis_config.graph_files.base_graph_hazard,
            )
            return MultiLinkRedundancy(_analysis_input)
        if analysis.analysis == AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION:
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file=analysis_config.graph_files.origins_destinations_graph,
            )
            return OptimalRouteOriginDestination(_analysis_input)
        if analysis.analysis == AnalysisLossesEnum.MULTI_LINK_ORIGIN_DESTINATION:
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file_hazard=analysis_config.graph_files.origins_destinations_graph_hazard,
            )
            return MultiLinkOriginDestination(_analysis_input)
        if (
            analysis.analysis
            == AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION
        ):
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file_hazard=analysis_config.graph_files.origins_destinations_graph_hazard,
            )
            return OptimalRouteOriginClosestDestination(analysis_input=_analysis_input)
        if (
            analysis.analysis
            == AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION
        ):
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file=analysis_config.graph_files.origins_destinations_graph,
                graph_file_hazard=analysis_config.graph_files.origins_destinations_graph_hazard,
            )
            return MultiLinkOriginClosestDestination(_analysis_input)
        if analysis.analysis == AnalysisLossesEnum.SINGLE_LINK_LOSSES:
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file=analysis_config.graph_files.base_graph_hazard,
                graph_file_hazard=analysis_config.graph_files.base_graph_hazard,
            )
            return Losses(_analysis_input, analysis_config)
        if analysis.analysis == AnalysisLossesEnum.MULTI_LINK_LOSSES:
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file_hazard=analysis_config.graph_files.base_graph_hazard,
            )

            return Losses(_analysis_input, analysis_config)
        if analysis.analysis == AnalysisLossesEnum.MULTI_LINK_ISOLATED_LOCATIONS:
            _analysis_input = AnalysisInputWrapper.from_input(
                analysis=analysis,
                analysis_config=analysis_config,
                graph_file_hazard=analysis_config.graph_files.base_graph_hazard,
            )
            return MultiLinkIsolatedLocations(_analysis_input)
        raise NotImplementedError(f"Analysis {analysis.analysis} not implemented")
