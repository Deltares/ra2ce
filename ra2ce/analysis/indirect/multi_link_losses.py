from pathlib import Path

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.loss_type_enum import LossTypeEnum
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.multi_link_redundancy import MultiLinkRedundancy
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames


class MultiLinkLosses(AnalysisIndirectProtocol):
    analysis: AnalysisSectionLosses
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames
    _analysis_input: AnalysisInputWrapper

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names
        self._analysis_input = analysis_input

    def execute(self) -> GeoDataFrame:
        """Calculates the multi-link redundancy losses of a NetworkX graph.

        The function removes all links of a variable that have a minimum value
        of min_threshold. For each link it calculates the alternative path, if
        any available. This function only removes one group at the time and saves the data from removing that group.

        Returns:
            GeoDataFrame: The results of the analysis aggregated into a table.
        """
        gdf = MultiLinkRedundancy(self._analysis_input).execute()

        losses_fn = self.static_path.joinpath("hazard", self.analysis.loss_per_distance)
        losses_df = pd.read_excel(losses_fn, sheet_name="Sheet1")

        if self.analysis.loss_type == LossTypeEnum.CATEGORIZED:
            disruption_fn = self.static_path.joinpath(
                "hazard", self.analysis.disruption_per_category
            )
            disruption_df = pd.read_excel(disruption_fn, sheet_name="Sheet1")
            road_classes = [x for x in disruption_df.columns if "class" in x]

        results = []
        for hazard in self.hazard_names.names:
            hazard_name = self.hazard_names.get_name(hazard)

            _gdf = gdf.loc[gdf["hazard"] == hazard_name].copy()
            if (
                self.analysis.loss_type == LossTypeEnum.UNIFORM
            ):  # assume uniform threshold for disruption
                for col in self.analysis.traffic_cols:
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    _gdf.loc[_gdf["connected"] == 1, col + "_losses_detour"] = (
                        _gdf[col]
                        * _gdf["diff_dist"]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "cost"
                        ].values[0]
                        * self.analysis.uniform_duration
                        / 24
                    )
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy_per_vehicle[person/veh] * duration_disruption[hour] / 24[hour/day] * gdp_percapita_per_day [USD/person]
                    _gdf.loc[_gdf["connected"] == 0, col + "_losses_nodetour"] = (
                        _gdf[col]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "occupancy"
                        ].values[0]
                        * self.analysis.gdp_percapita
                        * self.analysis.uniform_duration
                        / 24
                    )
                _gdf["total_losses_" + hazard_name] = np.nansum(
                    _gdf[
                        [
                            x
                            for x in _gdf.columns
                            if ("losses" in x) and ("total" not in x)
                        ]
                    ],
                    axis=1,
                )

            if (
                self.analysis.loss_type == LossTypeEnum.CATEGORIZED
            ):  # assume different disruption type depending on flood depth and road types
                disruption_df["class_identifier"] = ""
                _gdf["class_identifier"] = ""
                for i, road_class in enumerate(road_classes):
                    disruption_df["class_identifier"] += disruption_df[road_class]
                    _gdf["class_identifier"] += _gdf[road_class[6:]]
                    if i < len(road_classes) - 1:
                        disruption_df["class_identifier"] += "_nextclass_"
                        _gdf["class_identifier"] += "_nextclass_"

                all_road_categories = np.unique(_gdf["class_identifier"])
                _gdf["duration_disruption"] = 0

                for lb in np.unique(disruption_df["lower_bound"]):
                    disruption_df_ = disruption_df.loc[
                        disruption_df["lower_bound"] == lb
                    ]
                    ub = disruption_df_["upper_bound"].values[0]
                    if ub <= 0:
                        ub = 1e10
                    for road_cat in all_road_categories:
                        _gdf.loc[
                            (
                                _gdf[
                                    hazard_name
                                    + "_"
                                    + self.analysis.aggregate_wl.config_value
                                ]
                                > lb
                            )
                            & (
                                _gdf[
                                    hazard_name
                                    + "_"
                                    + self.analysis.aggregate_wl.config_value
                                ]
                                <= ub
                            )
                            & (_gdf["class_identifier"] == road_cat),
                            "duration_disruption",
                        ] = disruption_df_.loc[
                            disruption_df_["class_identifier"] == road_cat,
                            "duration_disruption",
                        ].values[
                            0
                        ]

                for col in self.analysis.traffic_cols:
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    _gdf.loc[_gdf["connected"] == 1, col + "_losses_detour"] = (
                        _gdf[col]
                        * _gdf["diff_dist"]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "cost"
                        ].values[0]
                        * _gdf["duration_disruption"]
                        / 24
                    )
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita[USD/person] * duration_disruption[hour] / 24[hour/day]
                    _gdf.loc[_gdf["connected"] == 0, col + "_losses_nodetour"] = (
                        _gdf[col]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "occupancy"
                        ].values[0]
                        * self.analysis.gdp_percapita
                        * _gdf["duration_disruption"]
                        / 24
                    )
                _gdf["total_losses_" + hazard_name] = np.nansum(
                    _gdf[
                        [
                            x
                            for x in _gdf.columns
                            if ("losses" in x) and ("total" not in x)
                        ]
                    ],
                    axis=1,
                )
            results.append(_gdf)

        return pd.concat(results, ignore_index=True)
