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
import math
from pathlib import Path

from geopandas import GeoDataFrame
from pandas import DataFrame

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
        _cost_df = self.run_cost()
        _benefit_df = self.run_benefit()

        return self.generate_result_wrapper(
            self.calculate_bc_ratio(_benefit_df, _cost_df)
        )

    def run_cost(self) -> DataFrame:
        """
        Calculate the link cost for all adaptation options.
        The unit cost is multiplied by the length of the link.
        If the hazard fraction cost is enabled, the cost is multiplied by the fraction of the link that is impacted.

        Returns:
            DataFrame: The result of the cost calculation.
        """
        _orig_gdf = self.graph_file_hazard.get_graph()
        _fraction_col = _orig_gdf.filter(regex="EV.*_fr").columns[0]

        _cost_df = _orig_gdf[["link_id"]].copy()
        for (
            _option,
            _cost,
        ) in self.adaptation_collection.calculate_options_unit_cost().items():
            _cost_df[_option.cost_col] = _orig_gdf.apply(
                lambda x, cost=_cost: x["length"] * cost, axis=1
            )
            # Only calculate the cost for the impacted fraction of the links.
            if self.analysis.hazard_fraction_cost:
                _cost_df[_option.cost_col] *= _orig_gdf[_fraction_col]

        return _cost_df

    def run_benefit(self) -> DataFrame:
        """
        Calculate the benefit for all adaptation options.

        Returns:
            DataFrame: The result of the benefit calculation.
        """
        return self.adaptation_collection.calculate_options_benefit()

    def calculate_bc_ratio(
        self, benefit_df: DataFrame, cost_df: DataFrame
    ) -> GeoDataFrame:
        """
        Calculate the benefit-cost ratio for all adaptation options.

        Args:
            benefit_df (DataFrame): Df containing the benefit of the adaptation options.
            cost_df (DataFrame): Df containing the cost of the adaptation options.

        Returns:
            GeoDataFrame: Gdf containing the benefit-cost ratio of the adaptation options,
                including the relevant attributes from the original graph (geometry).
        """

        def merge_columns(
            left_df: DataFrame, right_df: DataFrame, columns: list[str]
        ) -> DataFrame:
            # Merge 2 dataframes base on link_id
            _id_col = "link_id"

            # Add temporary key as the link_id to merge on contains inconsistent types (list[int] and int)
            _merge_col = "temp_key"

            left_df[_merge_col] = left_df[_id_col].apply(lambda x: str(x))
            # Not all columns are present in both dataframes, so only merge the relevant columns
            _columns = [_col for _col in columns if _col in left_df.columns]
            if not _columns:
                return right_df

            right_df[_merge_col] = right_df[_id_col].apply(lambda x: str(x))
            # Not each dataframe has the same entries in the link_id column, so use an outer merge
            _merged_df = right_df.merge(
                left_df[[_merge_col] + _columns],
                on=_merge_col,
                how="outer",
            ).fillna(math.nan)

            return _merged_df.drop(columns=[_merge_col])

        # Copy relevant columns from the original graph
        _orig_gdf = self.graph_file_hazard.get_graph()
        _bc_ratio_gdf = _orig_gdf[["link_id"]]
        _bc_ratio_gdf = merge_columns(
            _orig_gdf, _bc_ratio_gdf, ["geometry", "infra_type", "highway", "length"]
        )

        for _option in self.adaptation_collection.adaptation_options:
            # Copy benefit and cost column from the benefit and cost gdf
            _bc_ratio_gdf = merge_columns(
                benefit_df, _bc_ratio_gdf, [_option.benefit_col]
            )
            _bc_ratio_gdf = merge_columns(cost_df, _bc_ratio_gdf, [_option.cost_col])

            # Calculate BC-ratio
            _bc_ratio_gdf[_option.bc_ratio_col] = _bc_ratio_gdf[
                _option.benefit_col
            ].replace(float("nan"), 0) / _bc_ratio_gdf[_option.cost_col].replace(
                0, float("nan")
            )

        return GeoDataFrame(_bc_ratio_gdf).set_geometry("geometry")
