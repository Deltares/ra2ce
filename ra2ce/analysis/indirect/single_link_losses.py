from pathlib import Path

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.single_link_redundancy import SingleLinkRedundancy
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames


class SingleLinkLosses(AnalysisIndirectProtocol):
    graph_file: GraphFile
    analysis: AnalysisSectionIndirect
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames
    result: GeoDataFrame

    def __init__(
        self,
        graph_file: GraphFile,
        analysis: AnalysisSectionIndirect,
        input_path: Path,
        static_path: Path,
        output_path: Path,
        hazard_names: HazardNames,
    ) -> None:
        self.graph_file = graph_file
        self.analysis = analysis
        self.input_path = input_path
        self.static_path = static_path
        self.output_path = output_path
        self.hazard_names = hazard_names
        self.result = None

    def _single_link_losses_uniform(
        self,
        gdf: GeoDataFrame,
        analysis: AnalysisSectionIndirect,
        losses_df: pd.DataFrame,
    ):
        for hz in self.config.hazard_names:
            for col in analysis.traffic_cols:
                try:
                    assert gdf[col + "_detour_losses"]
                    assert gdf[col + "_nodetour_losses"]
                except Exception:
                    gdf[col + "_detour_losses"] = 0
                    gdf[col + "_nodetour_losses"] = 0
                # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle]  * duration_disruption[hour] / 24[hour/day]
                gdf.loc[
                    (gdf["detour"] == 1)
                    & (
                        gdf[hz + "_" + analysis.aggregate_wl.config_value]
                        > analysis.threshold
                    ),
                    col + "_detour_losses",
                ] += (
                    gdf[col]
                    * gdf["diff_dist"]
                    * losses_df.loc[losses_df["traffic_class"] == col, "cost"].values[0]
                    * analysis.uniform_duration
                    / 24
                )
                # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita_per_day[USD/person] * duration_disruption[hour] / 24[hour/day]
                gdf.loc[
                    (gdf["detour"] == 0)
                    & (
                        gdf[hz + "_" + analysis.aggregate_wl.config_value]
                        > analysis.threshold
                    ),
                    col + "_nodetour_losses",
                ] += (
                    gdf[col]
                    * losses_df.loc[
                        losses_df["traffic_class"] == col, "occupancy"
                    ].values[0]
                    * analysis.gdp_percapita
                    * analysis.uniform_duration
                    / 24
                )
            gdf["total_losses_" + hz] = np.nansum(
                gdf[[x for x in gdf.columns if ("losses" in x) and ("total" not in x)]],
                axis=1,
            )

    def _single_link_losses_categorized(
        self,
        gdf: GeoDataFrame,
        analysis: AnalysisSectionIndirect,
        losses_df: pd.DataFrame,
        disruption_df: pd.DataFrame,
    ):
        _road_classes = [x for x in disruption_df.columns if "class" in x]
        for hz in self.hazard_names.names_config:
            disruption_df["class_identifier"] = ""
            gdf["class_identifier"] = ""
            for i, road_class in enumerate(_road_classes):
                disruption_df["class_identifier"] += disruption_df[road_class]
                gdf["class_identifier"] += gdf[road_class[6:]]
                if i < len(_road_classes) - 1:
                    disruption_df["class_identifier"] += "_nextclass_"
                    gdf["class_identifier"] += "_nextclass_"

            _all_road_categories = np.unique(gdf["class_identifier"])
            gdf["duration_disruption"] = 0

            for lb in np.unique(disruption_df["lower_bound"]):
                disruption_df_ = disruption_df.loc[disruption_df["lower_bound"] == lb]
                ub = disruption_df_["upper_bound"].values[0]
                if ub <= 0:
                    ub = 1e10
                for road_cat in _all_road_categories:
                    gdf.loc[
                        (gdf[hz + "_" + analysis.aggregate_wl.config_value] > lb)
                        & (gdf[hz + "_" + analysis.aggregate_wl.config_value] <= ub)
                        & (gdf["class_identifier"] == road_cat),
                        "duration_disruption",
                    ] = disruption_df_.loc[
                        disruption_df_["class_identifier"] == road_cat,
                        "duration_disruption",
                    ].values[
                        0
                    ]

            for col in analysis.traffic_cols:
                try:
                    assert gdf[col + "_detour_losses"]
                    assert gdf[col + "_nodetour_losses"]
                except Exception:
                    gdf[col + "_detour_losses"] = 0
                    gdf[col + "_nodetour_losses"] = 0
                # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                gdf.loc[gdf["detour"] == 1, col + "_detour_losses"] += (
                    gdf[col]
                    * gdf["diff_dist"]
                    * losses_df.loc[losses_df["traffic_class"] == col, "cost"].values[0]
                    * gdf["duration_disruption"]
                    / 24
                )
                # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita[USD/person] * duration_disruption[hour] / 24[hour/day]
                gdf.loc[gdf["detour"] == 0, col + "_nodetour_losses"] += (
                    gdf[col]
                    * losses_df.loc[
                        losses_df["traffic_class"] == col, "occupancy"
                    ].values[0]
                    * analysis.gdp_percapita
                    * gdf["duration_disruption"]
                    / 24
                )
            gdf["total_losses_" + hz] = np.nansum(
                gdf[[x for x in gdf.columns if ("losses" in x) and ("total" not in x)]],
                axis=1,
            )

    def execute(self) -> GeoDataFrame:
        """Calculates single link disruption losses.

        Returns:
            GeoDataFrame: The results of the analysis aggregated into a table.
        """
        gdf = SingleLinkRedundancy(
            self.graph_file,
            self.analysis,
            self.input_path,
            self.static_path,
            self.output_path,
            self.hazard_names,
        ).execute()

        losses_fn = self.static_path.joinpath("hazard", self.analysis.loss_per_distance)
        losses_df = pd.read_excel(losses_fn, sheet_name="Sheet1")

        if self.analysis.loss_type == "uniform":
            # assume uniform threshold for disruption
            self._single_link_losses_uniform(gdf, self.analysis, losses_df)

        if self.analysis.loss_type == "categorized":
            _disruption_file = self.static_path.joinpath(
                "hazard", self.analysis.disruption_per_category
            )
            _disruption_df = pd.read_excel(_disruption_file, sheet_name="Sheet1")
            self._single_link_losses_categorized(
                gdf, self.analysis, losses_df, _disruption_df
            )

        return gdf
