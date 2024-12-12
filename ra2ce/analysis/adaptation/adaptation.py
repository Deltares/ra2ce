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
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class Adaptation(AnalysisBase, AnalysisDamagesProtocol):
    """
    Execute the adaptation analysis.
    For each adaptation option a damages and/or losses analysis is executed.
    """

    analysis: AnalysisSectionAdaptation
    graph_file_hazard: NetworkFile
    input_path: Path
    output_path: Path
    adaptation_collection: AdaptationOptionCollection

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
        analysis_config: AnalysisConfigWrapper,
    ):
        self.analysis = analysis_input.analysis
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.output_path = analysis_input.output_path
        self.adaptation_collection = AdaptationOptionCollection.from_config(
            analysis_config
        )
        self.output_path = analysis_input.output_path

    def execute(self) -> AnalysisResultWrapper:
        """
        Run the adaptation analysis.

        Returns:
            AnalysisResultWrapper: The result of the adaptation analysis.
        """
        _cost_gdf = self.run_cost()
        _benefit_gdf = self.run_benefit()

        return self.generate_result_wrapper(
            self.calculate_bc_ratio(_benefit_gdf, _cost_gdf)
        )

    def run_cost(self) -> GeoDataFrame:
        """
        Calculate the link cost for all adaptation options.
        The unit cost is multiplied by the length of the link.
        If the hazard fraction cost is enabled, the cost is multiplied by the fraction of the link that is impacted.

        Returns:
            GeoDataFrame: The result of the cost calculation.
        """
        _orig_gdf = self.graph_file_hazard.get_graph()
        _fraction_col = _orig_gdf.filter(regex="EV.*_fr").columns[0]

        _cost_gdf = GeoDataFrame()
        for (
            _option,
            _cost,
        ) in self.adaptation_collection.calculate_options_unit_cost().items():
            _cost_gdf[_option.cost_col] = _orig_gdf.apply(
                lambda x, cost=_cost: x["length"] * cost, axis=1
            )
            # Only calculate the cost for the impacted fraction of the links.
            if self.analysis.hazard_fraction_cost:
                _cost_gdf[_option.cost_col] *= _orig_gdf[_fraction_col]

        return _cost_gdf

    def run_benefit(self) -> GeoDataFrame:
        """
        Calculate the benefit for all adaptation options.

        Returns:
            GeoDataFrame: The result of the benefit calculation.
        """
        return self.adaptation_collection.calculate_options_benefit()

    def calculate_bc_ratio(
        self, benefit_gdf: GeoDataFrame, cost_gdf: GeoDataFrame
    ) -> GeoDataFrame:
        """
        Calculate the benefit-cost ratio for all adaptation options.

        Args:
            benefit_gdf (GeoDataFrame): Gdf containing the benefit of the adaptation options.
            cost_gdf (GeoDataFrame): Gdf containing the cost of the adaptation options.

        Returns:
            GeoDataFrame: Gdf containing the benefit-cost ratio of the adaptation options,
                including the relevant attributes from the original graph (geometry).
        """

        def copy_column(from_gdf: GeoDataFrame, col_name: str) -> None:
            if not col_name in from_gdf.columns:
                return
            benefit_gdf.insert(loc=0, column=col_name, value=from_gdf[col_name])

        # Copy relevant columns from the original graph
        _orig_gdf = self.graph_file_hazard.get_graph()
        benefit_gdf.set_geometry(_orig_gdf.geometry, inplace=True)
        for _col in ["length", "highway", "infra_type", "link_id"]:
            copy_column(_orig_gdf, _col)

        for _option in self.adaptation_collection.adaptation_options:
            # Copy cost columns from the cost gdf
            copy_column(cost_gdf, _option.cost_col)

            benefit_gdf[_option.bc_ratio_col] = benefit_gdf[
                _option.benefit_col
            ].replace(float("nan"), 0) / benefit_gdf[_option.cost_col].replace(
                0, float("nan")
            )

        return benefit_gdf
