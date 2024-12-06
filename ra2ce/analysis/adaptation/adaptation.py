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
from copy import deepcopy
from pathlib import Path

import numpy as np
from cleo.helpers import option
from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class Adaptation(AnalysisDamagesProtocol):
    """
    Execute the adaptation analysis.
    For each adaptation option a damages and losses analysis is executed.
    """

    analysis: AnalysisSectionAdaptation
    graph_file: NetworkFile
    input_path: Path
    output_path: Path
    adaptation_collection: AdaptationOptionCollection

    # TODO: add the proper protocol for the adaptation analysis.
    def __init__(
            self,
            analysis_input: AnalysisInputWrapper,
            analysis_config: AnalysisConfigWrapper,
    ):
        self.analysis = analysis_input.analysis
        self.graph_file = analysis_input.graph_file
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.adaptation_collection = AdaptationOptionCollection.from_config(
            analysis_config
        )

    def execute(self) -> GeoDataFrame:
        """
        Run the adaptation analysis.

        Returns:
            GeoDataFrame: The result of the adaptation analysis.
        """
        return self.calculate_bc_ratio()

    def run_cost(self) -> GeoDataFrame:
        """
                Calculate the unit cost for all adaptation options.

                Returns:
                    GeoDataFrame: The result of the cost calculation.
        """
        _cost_gdf = deepcopy(self.graph_file.get_graph())

        for (
                _option,
                _cost,
        ) in self.adaptation_collection.calculate_options_unit_cost().items():
            _cost_gdf[f"{_option.id}_cost"] = _cost_gdf.apply(
                lambda x, cost=_cost: x["length"] * cost, axis=1
            )

        return _cost_gdf

    def run_net_present_impact(self) -> GeoDataFrame:
        """
        Calculate the net present impact for all adaptation options for the entire time horizon.
        """
        # _impact_gdf = self.run_impact()
        for _option in self.adaptation_collection.adaptation_options:
            _impact_array = _impact_gdf[f"impact_{_option.id}"].to_numpy()

            def calc_net_impact_time_horizon(event_impact: float):
                _years_array = np.arange(0, self.adaptation_collection.time_horizon)
                _frequency_per_year = self.adaptation_collection.initial_frequency + _years_array * self.adaptation_collection.climate_factor
                _discount = (1 + self.adaptation_collection.discount_rate) ** _years_array

                _damage_per_year = event_impact * _frequency_per_year / _discount
                return np.sum(_damage_per_year)

            _net_impact_array = np.array([calc_net_impact_time_horizon(damage) for damage in _impact_array])
            _impact_gdf[f"net_present_impact_{_option.id}"] = _net_impact_array

        return _impact_gdf

    def run_benefit(self) -> GeoDataFrame:
        """
        Calculate the benefit for all adaptation options.

        Returns:
            GeoDataFrame: The result of the benefit calculation.
        """
        _benefit_gdf = deepcopy(self.graph_file.get_graph())

        return self.adaptation_collection.calculation_options_impact(_benefit_gdf)

    def calculate_bc_ratio(self) -> GeoDataFrame:
        """
        Calculate the benefit-cost ratio for all adaptation options.

        Returns:
            GeoDataFrame: The result of the benefit-cost ratio calculation.
        """
        _cost_gdf = self.run_cost()
        _benefit_gdf = self.run_benefit()

        # TODO: apply economic discounting
        # TODO: calculate B/C ratio
        # TODO: apply overlay

        return _cost_gdf
