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

import copy
import logging
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx
import pandas as pd
from pyproj import CRS
from shapely.geometry import LineString, MultiLineString
from tqdm import tqdm

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionIndirect,
)
from ra2ce.analyses.indirect.losses import Losses
from ra2ce.analyses.indirect.origin_closest_destination import OriginClosestDestination
from ra2ce.analyses.indirect.traffic_analysis.traffic_analysis_factory import (
    TrafficAnalysisFactory,
)
from ra2ce.common.io.readers.graph_pickle_reader import GraphPickleReader
from ra2ce.graph.networks_utils import buffer_geometry, graph_to_gdf, graph_to_gpkg


class IndirectAnalyses:
    """Indirect analyses that can be done with NetworkX graphs.

    Attributes:
        config: A dictionary with the configuration details on how to create and adjust the network.
        graphs: A dictionary with one or multiple NetworkX graphs.
    """

    config: AnalysisConfigData
    graphs: dict
    hazard_names_df: pd.DataFrame

    _file_name_key = "File name"
    _ra2ce_name_key = "RA2CE name"

    def __init__(self, config: AnalysisConfigData, graphs: list[Any]):
        self.config = config
        self.graphs = graphs
        if self.config.output_path.joinpath("hazard_names.xlsx").is_file():
            self.hazard_names_df = pd.read_excel(
                self.config.output_path.joinpath("hazard_names.xlsx")
            )
            self.config.hazard_names = list(
                set(self.hazard_names_df[self._file_name_key])
            )
        else:
            self.hazard_names_df = pd.DataFrame(data=None)
            self.config.hazard_names = list()

    def single_link_redundancy(self, graph, analysis: AnalysisSectionIndirect):
        """This is the function to analyse roads with a single link disruption and an alternative route.

        Args:
            graph: The NetworkX graph to calculate the single link redundancy on.
            analysis: Dictionary of the configurations for the analysis.
        """
        # TODO adjust to the right names of the RA2CE tool
        # if 'road_usage_data_path' in InputDict:
        #     road_usage_data = pd.read_excel(InputDict.road_usage_data_path)
        #     road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
        #     aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
        # else:
        #     aadt_names = None
        #     road_usage_data = pd.DataFrame()

        # create a geodataframe from the graph
        gdf = osmnx.graph_to_gdfs(graph, nodes=False)

        # list for the length of the alternative routes
        alt_dist_list = []
        alt_nodes_list = []
        dif_dist_list = []
        detour_exist_list = []
        for e_remove in list(graph.edges.data(keys=True)):
            u, v, k, data = e_remove

            # if data['highway'] in attr_list:
            # remove the edge
            graph.remove_edge(u, v, k)

            if nx.has_path(graph, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(
                    graph, u, v, weight=analysis.weighing
                )
                alt_dist_list.append(alt_dist)

                # append alternative route nodes
                alt_nodes = nx.dijkstra_path(graph, u, v)
                alt_nodes_list.append(alt_nodes)

                # calculate the difference in distance
                dif_dist_list.append(alt_dist - data[analysis.weighing])

                detour_exist_list.append(1)
            else:
                alt_dist_list.append(np.NaN)
                alt_nodes_list.append(np.NaN)
                dif_dist_list.append(np.NaN)
                detour_exist_list.append(0)

            # add edge again to the graph
            graph.add_edge(u, v, k, **data)

        # Add the new columns to the geodataframe
        gdf["alt_dist"] = alt_dist_list
        gdf["alt_nodes"] = alt_nodes_list
        gdf["diff_dist"] = dif_dist_list
        gdf["detour"] = detour_exist_list

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return gdf

    def single_link_losses(
        self, gdf: gpd.GeoDataFrame, analysis: AnalysisSectionIndirect
    ):
        """Calculates single link disruption losses.

        Args:
            gdf: The network in GeoDataFrame format.
            analysis: Dictionary of the configurations for the analysis.
        """
        losses_fn = self.config.static_path.joinpath(
            "hazard", analysis.loss_per_distance
        )
        losses_df = pd.read_excel(losses_fn, sheet_name="Sheet1")

        if analysis.loss_type == "uniform":
            # assume uniform threshold for disruption
            self._single_link_losses_uniform(gdf, analysis, losses_df)

        if analysis.loss_type == "categorized":
            _disruption_file = self.config.static_path.joinpath(
                "hazard", analysis.disruption_per_category
            )
            _disruption_df = pd.read_excel(_disruption_file, sheet_name="Sheet1")
            self._single_link_losses_categorized(
                gdf, analysis, losses_df, _disruption_df
            )

        return gdf

    def _single_link_losses_uniform(
        self,
        gdf: gpd.GeoDataFrame,
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
                    & (gdf[hz + "_" + analysis.aggregate_wl] > analysis.threshold),
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
                    & (gdf[hz + "_" + analysis.aggregate_wl] > analysis.threshold),
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
        gdf: gpd.GeoDataFrame,
        analysis: AnalysisSectionIndirect,
        losses_df: pd.DataFrame,
        disruption_df: pd.DataFrame,
    ):
        _road_classes = [x for x in disruption_df.columns if "class" in x]
        for hz in self.config.hazard_names:
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
                        (gdf[hz + "_" + analysis.aggregate_wl] > lb)
                        & (gdf[hz + "_" + analysis.aggregate_wl] <= ub)
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

    def multi_link_redundancy(self, graph: dict, analysis: AnalysisSectionIndirect):
        """Calculates the multi-link redundancy of a NetworkX graph.

        The function removes all links of a variable that have a minimum value
        of min_threshold. For each link it calculates the alternative path, if
        any available. This function only removes one group at the time and saves the data from removing that group.

        Args:
            graph: The NetworkX graph to calculate the single link redundancy on.
            analysis: Dictionary of the configurations for the analysis.

        Returns:
            aggregated_results (GeoDataFrame): The results of the analysis aggregated into a table.
        """
        results = []
        master_graph = copy.deepcopy(graph)
        for hazard in self.config.hazard_names:
            hazard_name = self.hazard_names_df.loc[
                self.hazard_names_df[self._file_name_key] == hazard,
                self._ra2ce_name_key,
            ].values[0]

            graph = copy.deepcopy(master_graph)
            # Create a geodataframe from the full graph
            gdf = osmnx.graph_to_gdfs(master_graph, nodes=False)
            if "rfid" in gdf:
                gdf["rfid"] = gdf["rfid"].astype(str)

            # Create the edgelist that consist of edges that should be removed
            edges_remove = [
                e for e in graph.edges.data(keys=True) if hazard_name in e[-1]
            ]
            edges_remove = [e for e in edges_remove if (e[-1][hazard_name] is not None)]
            edges_remove = [
                e
                for e in edges_remove
                if (e[-1][hazard_name] > float(analysis.threshold))
                & ("bridge" not in e[-1])
            ]

            graph.remove_edges_from(edges_remove)

            columns = ["u", "v", "alt_dist", "alt_nodes", "connected"]

            if "rfid" in gdf:
                columns.insert(2, "rfid")

            df_calculated = pd.DataFrame(columns=columns)

            for edges in edges_remove:
                u, v, k, edata = edges

                if nx.has_path(graph, u, v):
                    alt_dist = nx.dijkstra_path_length(
                        graph, u, v, weight=analysis.weighing
                    )
                    alt_nodes = nx.dijkstra_path(graph, u, v)
                    connected = 1
                else:
                    alt_dist, alt_nodes, connected = np.NaN, np.NaN, 0

                data = {
                    "u": [u],
                    "v": [v],
                    "alt_dist": [alt_dist],
                    "alt_nodes": [alt_nodes],
                    "connected": [connected],
                }

                if "rfid" in gdf:
                    data["rfid"] = [str(edata["rfid"])]

                df_calculated = pd.concat(
                    [df_calculated, pd.DataFrame(data)], ignore_index=True
                )
            # Merge the dataframes
            if "rfid" in gdf:
                gdf = gdf.merge(df_calculated, how="left", on=["u", "v", "rfid"])
            else:
                gdf = gdf.merge(df_calculated, how="left", on=["u", "v"])

            # calculate the difference in distance
            # previously here you would find if dist == dist which is a critical bug. Replaced by just verifying dist is a value.
            gdf["diff_dist"] = [
                dist - length if dist else np.NaN
                for (dist, length) in zip(gdf["alt_dist"], gdf[analysis.weighing])
            ]

            gdf["hazard"] = hazard_name

            results.append(gdf)

        aggregated_results = pd.concat(results, ignore_index=True)
        return aggregated_results

    def multi_link_losses(self, gdf, analysis: AnalysisSectionIndirect):
        """Calculates the multi-link redundancy losses of a NetworkX graph.

        The function removes all links of a variable that have a minimum value
        of min_threshold. For each link it calculates the alternative path, if
        any available. This function only removes one group at the time and saves the data from removing that group.

        Args:
            graph: The NetworkX graph to calculate the single link redundancy on.
            analysis: Dictionary of the configurations for the analysis.

        Returns:
            aggregated_results (GeoDataFrame): The results of the analysis aggregated into a table.
        """
        losses_fn = self.config.static_path.joinpath(
            "hazard", analysis.loss_per_distance
        )
        losses_df = pd.read_excel(losses_fn, sheet_name="Sheet1")

        if analysis.loss_type == "categorized":
            disruption_fn = self.config.static_path.joinpath(
                "hazard", analysis.disruption_per_category
            )
            disruption_df = pd.read_excel(disruption_fn, sheet_name="Sheet1")
            road_classes = [x for x in disruption_df.columns if "class" in x]

        results = []
        for hazard in self.config.hazard_names:
            hazard_name = self.hazard_names_df.loc[
                self.hazard_names_df[self._file_name_key] == hazard,
                self._ra2ce_name_key,
            ].values[0]

            gdf_ = gdf.loc[gdf["hazard"] == hazard_name].copy()
            if (
                analysis.loss_type == "uniform"
            ):  # assume uniform threshold for disruption
                for col in analysis.traffic_cols:
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    gdf_.loc[gdf_["connected"] == 1, col + "_losses_detour"] = (
                        gdf_[col]
                        * gdf_["diff_dist"]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "cost"
                        ].values[0]
                        * analysis.uniform_duration
                        / 24
                    )
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy_per_vehicle[person/veh] * duration_disruption[hour] / 24[hour/day] * gdp_percapita_per_day [USD/person]
                    gdf_.loc[gdf_["connected"] == 0, col + "_losses_nodetour"] = (
                        gdf_[col]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "occupancy"
                        ].values[0]
                        * analysis.gdp_percapita
                        * analysis.uniform_duration
                        / 24
                    )
                gdf_["total_losses_" + hz] = np.nansum(
                    gdf_[
                        [
                            x
                            for x in gdf_.columns
                            if ("losses" in x) and ("total" not in x)
                        ]
                    ],
                    axis=1,
                )

            if (
                analysis.loss_type == "categorized"
            ):  # assume different disruption type depending on flood depth and road types
                disruption_df["class_identifier"] = ""
                gdf_["class_identifier"] = ""
                for i, road_class in enumerate(road_classes):
                    disruption_df["class_identifier"] += disruption_df[road_class]
                    gdf_["class_identifier"] += gdf_[road_class[6:]]
                    if i < len(road_classes) - 1:
                        disruption_df["class_identifier"] += "_nextclass_"
                        gdf_["class_identifier"] += "_nextclass_"

                all_road_categories = np.unique(gdf_["class_identifier"])
                gdf_["duration_disruption"] = 0

                for lb in np.unique(disruption_df["lower_bound"]):
                    disruption_df_ = disruption_df.loc[
                        disruption_df["lower_bound"] == lb
                    ]
                    ub = disruption_df_["upper_bound"].values[0]
                    if ub <= 0:
                        ub = 1e10
                    for road_cat in all_road_categories:
                        gdf_.loc[
                            (gdf_[hz + "_" + analysis.aggregate_wl] > lb)
                            & (gdf_[hz + "_" + analysis.aggregate_wl] <= ub)
                            & (gdf_["class_identifier"] == road_cat),
                            "duration_disruption",
                        ] = disruption_df_.loc[
                            disruption_df_["class_identifier"] == road_cat,
                            "duration_disruption",
                        ].values[
                            0
                        ]

                for col in analysis.traffic_cols:
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    gdf_.loc[gdf_["connected"] == 1, col + "_losses_detour"] = (
                        gdf_[col]
                        * gdf_["diff_dist"]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "cost"
                        ].values[0]
                        * gdf_["duration_disruption"]
                        / 24
                    )
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita[USD/person] * duration_disruption[hour] / 24[hour/day]
                    gdf_.loc[gdf_["connected"] == 0, col + "_losses_nodetour"] = (
                        gdf_[col]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "occupancy"
                        ].values[0]
                        * analysis.gdp_percapita
                        * gdf_["duration_disruption"]
                        / 24
                    )
                gdf_["total_losses_" + hz] = np.nansum(
                    gdf_[
                        [
                            x
                            for x in gdf_.columns
                            if ("losses" in x) and ("total" not in x)
                        ]
                    ],
                    axis=1,
                )
            results.append(gdf_)

        aggregated_results = pd.concat(results, ignore_index=True)
        return aggregated_results

    @staticmethod
    def extract_od_nodes_from_graph(
        graph: nx.classes.MultiGraph,
    ) -> list[tuple[str, str]]:
        """
        Extracts all Origin - Destination nodes from the graph, prevents from entries
        with list of nodes for a node.

        Args:
            graph (nx.classes.MultiGraph): Graph containing origin-destination nodes.

        Returns:
            list[tuple[str, str]]]: List containing tuples of origin - destination node combinations.
        """
        _od_nodes = []
        for n, v in graph.nodes(data=True):
            if "od_id" not in v:
                continue
            _o_node_list = list(map(lambda x: (n, x), v["od_id"].split(",")))
            _od_nodes.extend(_o_node_list)
        return _od_nodes

    def _get_origin_destination_pairs(
        self, graph: nx.classes.MultiGraph
    ) -> list[tuple[int, str], tuple[int, str]]:
        od_path = self.config.static_path.joinpath(
            "output_graph", "origin_destination_table.feather"
        )
        od = gpd.read_feather(od_path)
        od_pairs = [
            (a, b)
            for a in od.loc[od["o_id"].notnull(), "o_id"]
            for b in od.loc[od["d_id"].notnull(), "d_id"]
        ]
        all_nodes = self.extract_od_nodes_from_graph(graph)
        od_nodes = []
        for aa, bb in od_pairs:
            # it is possible that there are multiple origins/destinations at the same 'entry-point' in the road
            od_nodes.append(
                (
                    [
                        (n, n_name)
                        for n, n_name in all_nodes
                        if (n_name == aa) | (aa in n_name)
                    ][0],
                    [
                        (n, n_name)
                        for n, n_name in all_nodes
                        if (n_name == bb) | (bb in n_name)
                    ][0],
                )
            )
        return od_nodes

    def optimal_route_origin_destination(
        self, graph: nx.classes.MultiGraph, analysis: AnalysisSectionIndirect
    ) -> gpd.GeoDataFrame:
        # create list of origin-destination pairs
        od_nodes = self._get_origin_destination_pairs(graph)
        pref_routes = find_route_ods(graph, od_nodes, analysis.weighing)
        return pref_routes

    def optimal_route_od_link(
        self,
        road_network: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        equity: pd.DataFrame,
    ) -> pd.DataFrame:
        return TrafficAnalysisFactory.get_analysis(
            road_network,
            od_table,
            self.config.origins_destinations.destinations_names,
            equity,
        ).optimal_route_od_link()

    def multi_link_origin_destination(self, graph, analysis: AnalysisSectionIndirect):
        """Calculates the connectivity between origins and destinations"""
        od_nodes = self._get_origin_destination_pairs(graph)

        all_results = []
        for hazard in self.config.hazard_names:
            hazard_name = self.hazard_names_df.loc[
                self.hazard_names_df[self._file_name_key] == hazard,
                self._ra2ce_name_key,
            ].values[0]

            graph_hz = copy.deepcopy(graph)

            # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
            edges_remove = [
                e for e in graph.edges.data(keys=True) if hazard_name in e[-1]
            ]
            edges_remove = [e for e in edges_remove if (e[-1][hazard_name] is not None)]
            edges_remove = [
                e
                for e in edges_remove
                if (e[-1][hazard_name] > float(analysis.threshold))
                & ("bridge" not in e[-1])
            ]
            graph_hz.remove_edges_from(edges_remove)

            # convert the networkx graph to igraph object to speed up the route finding algorithm
            # igraph_hz = ig.Graph.from_networkx(igraph_hz)

            # Find the routes
            od_routes = find_route_ods(graph_hz, od_nodes, analysis.weighing)
            od_routes["hazard"] = hazard_name
            all_results.append(od_routes)

        all_results = pd.concat(all_results, ignore_index=True)
        return all_results

    def multi_link_origin_destination_impact(self, gdf, gdf_ori):
        """Calculates some default indicators that quantify the impacts of disruptions to origin-destination flows
        The function outputs the following file:

        1. gdf_ori (multi_link_origin_destination_impact.csv), containing the following information:
            - origin and destination node
            - length: initial shortest path length before disruptions
            - length_hazardName: shortest path length after disruption
            - diff_length_hazardName: increase in shortest path length after disruption (length_hazardName - length)
            - diff_length_hazardName_pc: same as above, but as a fraction of initial length

        2. diff_df (multi_link_origin_destination_impact_summary.csv), containing the following information:
            - hazard: hazard name
            - od_disconnected_abs: number of OD disconnected
            - od_disconnected_pc (%): percentage of OD disconnected
            - origin_disconnected_abs: number of origin points disconnected
            - origin_disconnected_pc (%): percentage of origin points disconnected
            - destination_disconnected_abs: number of destination points disconnected
            - destination_disconnected_pc (%): percentage of destination points disconnected
            - max_increase_abs: maximum increase in travel length across all OD pairs
            - mean_increase_abs: mean increase in travel length across all OD pairs
            - median_increase_abs: median increase in travel length across all OD pairs
            - max_increase_pc, mean_increase_pc, median_increase_pc (%): same as above three, but as a percentage relative to no-hazard
        """

        hazard_list = np.unique(gdf["hazard"])

        # calculate number of disconnected origin, destination, and origin-destination pair
        # TODO: there seems to be an issue in calculating origin_count and destination_count where origin and destination nodes are the same, e.g., A_25,B_1
        gdf["OD"] = gdf["origin"] + gdf["destination"]
        gdf_ori["OD"] = gdf_ori["origin"] + gdf_ori["destination"]
        # origin
        gdf_ori["origin_count"] = gdf_ori["origin"].apply(lambda x: len(x.split(",")))
        init_origins = gdf_ori.groupby("origin")["origin_count"].sum()
        del gdf_ori["origin_count"]
        # destination
        gdf_ori["destination_count"] = gdf_ori["destination"].apply(
            lambda x: len(x.split(","))
        )
        init_destinations = gdf_ori.groupby("destination")["destination_count"].sum()
        del gdf_ori["destination_count"]
        # od pairs
        init_od_pairs = init_origins * init_destinations
        abs_od_disconnected = []
        share_od_disconnected = []
        abs_origin_disconnected = []
        share_origin_disconnected = []
        abs_destination_disconnected = []
        share_destination_disconnected = []
        for hz in hazard_list:
            gdf_ = gdf.loc[gdf["hazard"] == hz]

            gdf_["origin_count"] = gdf_["origin"].apply(lambda x: len(x.split(",")))
            remaining_origins = gdf_.groupby("origin")["origin_count"].sum()
            del gdf_["origin_count"]
            diff_origins = init_origins - remaining_origins
            abs_origin_disconnected.append(diff_origins)
            share_origin_disconnected.append(100 * diff_origins / init_origins)

            gdf_["destination_count"] = gdf_["destination"].apply(
                lambda x: len(x.split(","))
            )
            remaining_destinations = gdf_.groupby("destination")[
                "destination_count"
            ].sum()
            del gdf_["destination_count"]
            diff_destinations = init_destinations - remaining_destinations
            abs_destination_disconnected.append(diff_destinations)
            share_destination_disconnected.append(
                100 * diff_destinations / init_destinations
            )

            remaining_od_pairs = remaining_origins * remaining_destinations
            diff_od_pairs = init_od_pairs - remaining_od_pairs
            abs_od_disconnected.append(diff_od_pairs)
            share_od_disconnected.append(100 * diff_od_pairs / init_od_pairs)

        # calculate change in travel time/distance
        max_increase_abs = []
        min_increase_abs = []
        mean_increase_abs = []
        median_increase_abs = []
        max_increase_pc = []
        min_increase_pc = []
        mean_increase_pc = []
        median_increase_pc = []
        for hz in hazard_list:
            gdf_ = gdf.loc[gdf["hazard"] == hz][["OD", "length"]]
            gdf_.columns = ["OD", "length_" + hz]
            gdf_ori = gdf_ori.merge(gdf_, how="left", on="OD")
            gdf_ori.drop_duplicates(subset="OD", inplace=True)
            gdf_ori["diff_length_" + hz] = gdf_ori["length_" + hz] - gdf_ori["length"]
            gdf_ori["diff_length_" + hz + "_pc"] = (
                100 * gdf_ori["diff_length_" + hz] / gdf_ori["length"]
            )

            max_increase_abs.append(np.nanmax(gdf_ori["diff_length_" + hz]))
            min_increase_abs.append(np.nanmin(gdf_ori["diff_length_" + hz]))
            mean_increase_abs.append(np.nanmean(gdf_ori["diff_length_" + hz]))
            median_increase_abs.append(np.nanmedian(gdf_ori["diff_length_" + hz]))

            max_increase_pc.append(np.nanmax(gdf_ori["diff_length_" + hz + "_pc"]))
            min_increase_pc.append(np.nanmin(gdf_ori["diff_length_" + hz + "_pc"]))
            mean_increase_pc.append(np.nanmean(gdf_ori["diff_length_" + hz + "_pc"]))
            median_increase_pc.append(
                np.nanmedian(gdf_ori["diff_length_" + hz + "_pc"])
            )

        diff_df = pd.DataFrame()
        diff_df["hazard"] = hazard_list

        diff_df["od_disconnected_abs"] = abs_od_disconnected
        diff_df["od_disconnected_pc (%)"] = share_od_disconnected
        diff_df["origin_disconnected_abs"] = abs_origin_disconnected
        diff_df["origin_disconnected_pc (%)"] = share_origin_disconnected
        diff_df["destination_disconnected_abs"] = abs_destination_disconnected
        diff_df["destination_disconnected_pc (%)"] = share_destination_disconnected

        diff_df["max_increase_abs"] = max_increase_abs
        diff_df["min_increase_abs"] = min_increase_abs
        diff_df["mean_increase_abs"] = mean_increase_abs
        diff_df["median_increase_abs"] = median_increase_abs
        diff_df["max_increase_pc (%)"] = max_increase_pc
        diff_df["min_increase_pc (%)"] = min_increase_pc
        diff_df["mean_increase_pc (%)"] = mean_increase_pc
        diff_df["median_increase_pc (%)"] = median_increase_pc

        return diff_df, gdf_ori

    def multi_link_origin_destination_regional_impact(self, gdf_ori):
        """
        Aggregation of the impacts of disruptions at region level
        Users need to specify 'region' and 'region_var' attributes in the network.ini file
        See the Pontianak case study for an example

        The function outputs the following files:
        1. multi_link_origin_destination_regional_impact.csv
            Impacts of disruption aggregated for each origin node. Region information (to which region an origin node belongs) is retained

        2. multi_link_origin_destination_regional_impact_summary.csv
            Impacts of disruption aggregated for each region.

        In both files, the following information is stored:
            - init_length: initial average length to all destination nodes (for each origin node and for each region)
            - init_destination: initial number of destination nodes
            - hazardName_pc_increase: average increase in travel time to all destination nodes (percentage relative to initial travel time, for each origin node and for each region)
            - hazardName_pc_disconnect: average number of OD pairs disconnected (relative to initial number of OD pairs, for each origin node and for each region)
        """

        gdf_ori_ = gdf_ori.copy()

        # read origin points
        origin_fn = Path(self.config.static_path).joinpath(
            "output_graph", "origin_destination_table.gpkg"
        )
        origin = gpd.read_file(origin_fn, engine="pyogrio")
        index = [isinstance(x, str) for x in origin["o_id"]]
        origin = origin[index]
        origin.reset_index(inplace=True, drop=True)

        # record where each origin point resides
        origin_mapping = {}
        for o in np.unique(origin["o_id"]):
            r = origin.loc[origin["o_id"] == o, "region"].values[0]
            origin_mapping.update({o: r})

        # record impact to each region
        origin_impact_master = pd.DataFrame()
        for r in np.unique(origin["region"]):
            origin_points = list(origin.loc[origin["region"] == r, "o_id"].values)
            for o in origin_points:
                origin_impact_tosave = pd.DataFrame()
                origin_impact_tosave.loc[0, "o_id"] = o
                origin_impact_tosave.loc[0, "region"] = r

                origin_impact = gdf_ori_.loc[gdf_ori_["origin"].str.contains(o)]

                # initial condition
                origin_impact_tosave.loc[0, "init_length"] = np.mean(
                    origin_impact["length"]
                )
                origin_impact_tosave.loc[0, "init_destination"] = len(
                    np.unique(origin_impact["destination"])
                )

                # impact of each hazard
                for col in origin_impact.columns:
                    if "_pc" in col:
                        delta = np.nanmean(origin_impact[col])
                        if delta < 0:
                            delta = 0
                        origin_impact_tosave.loc[0, col[12:] + "_increase"] = delta

                        disconnected = origin_impact[col].isna().sum()
                        origin_impact_tosave.loc[0, col[12:] + "_disconnect"] = (
                            100
                            * disconnected
                            / origin_impact_tosave["init_destination"].values[0]
                        )

                origin_impact_master = origin_impact_master.append(origin_impact_tosave)

        region_impact_master = origin_impact_master[origin_impact_master.columns[1:]]
        region_impact_master = region_impact_master.groupby(by="region").mean()

        return origin_impact_master, region_impact_master

    def multi_link_isolated_locations(
        self, graph: nx.Graph, analysis: AnalysisSectionIndirect, crs=4326
    ) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
        """
        This function identifies locations that are flooded or isolated due to the disruption of the network caused by a hazard.
        It iterates over multiple hazard scenarios, modifies the graph to represent direct and indirect impacts, and then
        spatially joins the impacted network with the location data to find out which locations are affected.

        Args:
            graph (nx.Graph): The original graph representing the network, with additional hazard information.
            analysis (dict): The configuration of the analysis, which contains the threshold for considering a hazard impact significant.
            crs (int, optional): The coordinate reference system used for geographical data. Defaults to 4326 (WGS84).

        Returns:
            tuple (gpd.GeoDataFrame, pd.DataFrame): A tuple containing the location GeoDataFrame updated with hazard impacts,
                and a DataFrame summarizing the impacts per location category.
        """

        # Load the point shapefile with the locations of which the isolated locations should be identified.
        locations = gpd.read_feather(
            self.config.static_path.joinpath("output_graph", "locations_hazard.feather")
        )
        # TODO PUT CRS IN DOCUMENTATION OR MAKE CHANGABLE
        # reproject the datasets to be able to make a buffer in meters
        nearest_utm = utm_crs(locations.total_bounds)

        # create an empty list to append the df_aggregation to
        aggregation = pd.DataFrame()
        for i, hazard in enumerate(self.config.hazard_names):
            # for each hazard event
            hazard_name = self.hazard_names_df.loc[
                self.hazard_names_df[self._file_name_key] == hazard,
                self._ra2ce_name_key,
            ].values[0]

            graph_hz_direct = copy.deepcopy(graph)
            graph_hz_indirect = copy.deepcopy(graph)

            # filter graph edges that are directly disrupted by the hazard(s), i.e. flooded
            edges = [e for e in graph.edges.data(keys=True) if hazard_name in e[-1]]
            edges_hz_direct = [
                e
                for e in edges
                if (e[-1][hazard_name] > float(analysis.threshold))
                & ("bridge" not in e[-1])
            ]
            edges_hz_indirect = [e for e in edges if e not in edges_hz_direct]

            # get indirect graph - remove the edges that are impacted by hazard directly
            graph_hz_indirect.remove_edges_from(edges_hz_direct)
            # get indirect graph without the largest component, i.e. isolated graph
            self.remove_edges_from_largest_component(graph_hz_indirect)

            # get direct graph - romove the edges that are impacted by hazard indirectly
            graph_hz_direct.remove_edges_from(edges_hz_indirect)

            # get isolated network
            network_hz_indirect = gpd.GeoDataFrame()
            if len(graph_hz_indirect.edges) > 0:
                network_hz_indirect = self.get_network_with_edge_fid(graph_hz_indirect)
                network_hz_indirect[f"i_type_{hazard_name[:-3]}"] = "isolated"
                # reproject the datasets to be able to make a buffer in meters
                network_hz_indirect = network_hz_indirect.set_crs(crs=crs)
                network_hz_indirect.to_crs(crs=nearest_utm, inplace=True)

            # get flooded network
            network_hz_direct = gpd.GeoDataFrame()
            if len(graph_hz_direct.edges) > 0:
                network_hz_direct = self.get_network_with_edge_fid(graph_hz_direct)
                network_hz_direct[f"i_type_{hazard_name[:-3]}"] = "flooded"
                # reproject the datasets to be able to make a buffer in meters
                network_hz_direct = network_hz_direct.set_crs(crs=crs)
                network_hz_direct.to_crs(crs=nearest_utm, inplace=True)

            # get hazard roads
            # merge buffer and set original crs
            results_hz_roads = gpd.GeoDataFrame(
                pd.concat([network_hz_direct, network_hz_indirect])
            )
            results_hz_roads = buffer_geometry(
                results_hz_roads, analysis.buffer_meters
            ).to_crs(crs=crs)
            # Save the output
            results_hz_roads.to_file(
                self.config.output_path.joinpath(
                    analysis.analysis, f"flooded_and_isolated_roads_{hazard_name}.gpkg"
                )
            )

            # relate the locations to network disruption due to hazard by spatial overlay
            results_hz_roads.reset_index(inplace=True)
            locations_hz = gpd.overlay(
                locations, results_hz_roads, how="intersection", keep_geom_type=True
            )

            # Replace nan with 0 for the water depth columns
            # TODO: this should always be done in hazard class
            locations_hz[hazard_name] = locations_hz[hazard_name].fillna(0)

            # TODO: Put in analyses.ini file a variable to set the threshold for locations that are not isolated when they are flooded.
            # Extract the flood depth of the locations
            # intersect = intersect.loc[intersect[hazard_name] > analysis.threshold_locations]

            # get location stats
            df_aggregation = self._summarize_locations(
                locations_hz,
                cat_col=analysis.category_field_name,
                hazard_id=hazard_name[:-3],
            )

            # add to exisiting results
            aggregation = pd.concat([aggregation, df_aggregation], axis=0)

        # Set the locations_hz geopandas dataframe back to the original crs
        locations_hz.to_crs(crs=crs, inplace=True)

        return locations_hz, aggregation

    def remove_edges_from_largest_component(self, disconnected_graph: nx.Graph) -> None:
        """
        This function removes all edges from the largest connected component of a graph.

        Args:
            disconnected_graph (nx.Graph): The graph from which to remove the edges.
        """
        connected_components = list(
            c for c in nx.connected_components(disconnected_graph)
        )
        connected_components_size = list(
            len(c) for c in nx.connected_components(disconnected_graph)
        )

        largest_comp_index = connected_components_size.index(
            max(connected_components_size)
        )
        edges_from_lagest_component = list(
            disconnected_graph.subgraph(
                connected_components[largest_comp_index]
            ).edges()
        )
        disconnected_graph.remove_edges_from(edges_from_lagest_component)

    def get_network_with_edge_fid(self, graph: nx.Graph) -> gpd.GeoDataFrame:
        """
        This function converts a NetworkX graph into a GeoDataFrame representing the network.
        It also constructs an 'edge_fid' column based on the 'node_A' and 'node_B' columns, following a specific convention.

        Args:
            G (nx.Graph): The NetworkX graph to be converted.

        Returns:
            gpd.GeoDataFrame: The resulting GeoDataFrame, with an added 'edge_fid' column.
        """
        network = graph_to_gdf(graph)[0]
        # TODO: add making "edges_fid" (internal convention) to graph_to_gdf
        if all(c_idx in network.index.names for c_idx in ["u", "v"]):
            network["edge_fid"] = [f"{na}_{nb}" for (na, nb, _) in network.index]
        elif all(c_idx in network.columns for c_idx in ["node_A", "node_B"]):
            # shapefiles
            network["edge_fid"] = [
                f"{na}_{nb}" for na, nb in network["node_A", "node_B"].values
            ]
        return network[["edge_fid", "geometry"]]

    def _summarize_locations(
        self, locations: gpd.GeoDataFrame, cat_col: str, hazard_id: str
    ) -> pd.DataFrame:
        """
        This function summarizes the hazard impacts on different categories of locations.
        It adds a counter for each hazard type and aggregates the data per category.

        Args:
            locations (gpd.GeoDataFrame): A GeoDataFrame containing the locations and their hazard impacts.
            cat_col (str): The column name in the locations GeoDataFrame that represents the location categories.
            hazard_id (str): The identifier for the hazard being considered.

        Returns:
            pd.DataFrame: A DataFrame summarizing the number of isolated locations per category for the given hazard.
        """
        # add counter
        locations[f"i_{hazard_id}"] = 1  # add counter
        # make an overview of the locations, aggregated per category
        df_aggregation = (
            locations.groupby(by=[cat_col, f"i_type_{hazard_id}"])[f"i_{hazard_id}"]
            .sum()
            .reset_index()
        )
        df_aggregation["hazard"] = hazard_id
        df_aggregation.rename(columns={f"i_{hazard_id}": "nr_isolated"}, inplace=True)
        return df_aggregation

    def execute(self):
        """Executes the indirect analysis."""
        _pickle_reader = GraphPickleReader()
        for analysis in self.config.indirect:
            logging.info(
                f"----------------------------- Started analyzing '{analysis.name}'  -----------------------------"
            )
            starttime = time.time()
            gdf = pd.DataFrame()
            opt_routes = None
            _output_path = self.config.output_path.joinpath(analysis.analysis)

            def _save_gpkg_analysis(
                base_graph,
                to_save_gdf: list[gpd.GeoDataFrame],
                to_save_gdf_names: list[str],
            ):
                for to_save, save_name in zip(to_save_gdf, to_save_gdf_names):
                    if not to_save.empty:
                        gpkg_path = _output_path.joinpath(
                            analysis.name.replace(" ", "_") + f"_{save_name}.gpkg"
                        )
                        save_gdf(to_save, gpkg_path)

                # Save the Graph
                gpkg_path_nodes = _output_path.joinpath(
                    analysis.name.replace(" ", "_") + "_results_nodes.gpkg"
                )
                gpkg_path_edges = _output_path.joinpath(
                    analysis.name.replace(" ", "_") + "_results_edges.gpkg"
                )
                graph_to_gpkg(base_graph, gpkg_path_edges, gpkg_path_nodes)

            if analysis.weighing == "distance":
                # The name is different in the graph.
                analysis.weighing = "length"
            _config_files = self.config.files
            if analysis.analysis == "single_link_redundancy":
                g = _pickle_reader.read(_config_files["base_graph"])
                gdf = self.single_link_redundancy(g, analysis)
            elif analysis.analysis == "multi_link_redundancy":
                g = _pickle_reader.read(_config_files["base_graph_hazard"])
                gdf = self.multi_link_redundancy(g, analysis)
            elif analysis.analysis == "optimal_route_origin_destination":
                g = _pickle_reader.read(_config_files["origins_destinations_graph"])
                gdf = self.optimal_route_origin_destination(g, analysis)

                if analysis.save_traffic and hasattr(
                    self.config.origins_destinations, "origin_count"
                ):
                    od_table = gpd.read_feather(
                        self.config.static_path.joinpath(
                            "output_graph", "origin_destination_table.feather"
                        )
                    )
                    _equity_weights_file = None
                    if analysis.equity_weight:
                        _equity_weights_file = self.config.static_path.joinpath(
                            "network", analysis.equity_weight
                        )
                    route_traffic_df = self.optimal_route_od_link(
                        gdf,
                        od_table,
                        TrafficAnalysisFactory.read_equity_weights(
                            _equity_weights_file
                        ),
                    )
                    impact_csv_path = _output_path.joinpath(
                        (analysis.name.replace(" ", "_") + "_link_traffic.csv"),
                    )
                    route_traffic_df.to_csv(impact_csv_path, index=False)
            elif analysis.analysis == "multi_link_origin_destination":
                g = _pickle_reader.read(
                    self.config.files["origins_destinations_graph_hazard"]
                )
                gdf = self.multi_link_origin_destination(g, analysis)
                g_not_disrupted = _pickle_reader.read(
                    self.config.files["origins_destinations_graph_hazard"]
                )
                gdf_not_disrupted = self.optimal_route_origin_destination(
                    g_not_disrupted, analysis
                )
                (
                    disruption_impact_df,
                    gdf_ori,
                ) = self.multi_link_origin_destination_impact(gdf, gdf_not_disrupted)
                try:
                    assert self.config.origins_destinations.region
                    (
                        regional_impact_df,
                        regional_impact_summary_df,
                    ) = self.multi_link_origin_destination_regional_impact(gdf_ori)
                    impact_csv_path = _output_path.joinpath(
                        (analysis.name.replace(" ", "_") + "_regional_impact.csv"),
                    )
                    regional_impact_df.to_csv(impact_csv_path, index=False)
                    impact_csv_path = _output_path.joinpath(
                        (
                            analysis.name.replace(" ", "_")
                            + "_regional_impact_summary.csv"
                        ),
                    )
                    regional_impact_summary_df.to_csv(impact_csv_path)
                except Exception:
                    pass
                impact_csv_path = _output_path.joinpath(
                    (analysis.name.replace(" ", "_") + "_impact.csv"),
                )
                del gdf_ori["geometry"]
                gdf_ori.to_csv(impact_csv_path, index=False)
                impact_csv_path = _output_path.joinpath(
                    (analysis.name.replace(" ", "_") + "_impact_summary.csv"),
                )
                disruption_impact_df.to_csv(impact_csv_path, index=False)
            elif analysis.analysis == "single_link_losses":
                g = _pickle_reader.read(self.config.files["base_graph_hazard"])
                gdf = self.single_link_redundancy(g, analysis)
                gdf = self.single_link_losses(gdf, analysis)
            elif analysis.analysis == "multi_link_losses":
                g = _pickle_reader.read(self.config.files["base_graph_hazard"])
                gdf = self.multi_link_redundancy(g, analysis)
                gdf = self.multi_link_losses(gdf, analysis)
            elif analysis.analysis == "optimal_route_origin_closest_destination":
                analyzer = OriginClosestDestination(
                    self.config, analysis, self.hazard_names_df
                )
                (
                    base_graph,
                    opt_routes,
                    destinations,
                ) = analyzer.optimal_route_origin_closest_destination()
                if analysis.save_gpkg:
                    # Save the GeoDataFrames
                    to_save_gdf = [destinations, opt_routes]
                    to_save_gdf_names = ["destinations", "optimal_routes"]
                    _save_gpkg_analysis(base_graph, to_save_gdf, to_save_gdf_names)

                if analysis.save_csv:
                    csv_path = _output_path.joinpath(
                        analysis.name.replace(" ", "_") + "_destinations.csv"
                    )
                    del destinations["geometry"]
                    destinations.to_csv(csv_path, index=False)

                    csv_path = _output_path.joinpath(
                        analysis.name.replace(" ", "_") + "_optimal_routes.csv"
                    )
                    del opt_routes["geometry"]
                    opt_routes.to_csv(csv_path, index=False)
            elif analysis.analysis == "multi_link_origin_closest_destination":
                analyzer = OriginClosestDestination(
                    self.config, analysis, self.hazard_names_df
                )

                if analysis.calculate_route_without_disruption:
                    (
                        base_graph,
                        opt_routes_without_hazard,
                        destinations,
                    ) = analyzer.optimal_route_origin_closest_destination()

                    if (
                        analyzer.config.files["origins_destinations_graph_hazard"]
                        is None
                    ):
                        origins = analyzer.load_origins()
                        opt_routes_with_hazard = gpd.GeoDataFrame(data=None)
                    else:
                        (
                            base_graph,
                            origins,
                            destinations,
                            agg_results,
                            opt_routes_with_hazard,
                        ) = analyzer.multi_link_origin_closest_destination()

                        (
                            opt_routes_with_hazard
                        ) = analyzer.difference_length_with_without_hazard(
                            opt_routes_with_hazard, opt_routes_without_hazard
                        )

                else:
                    (
                        base_graph,
                        origins,
                        destinations,
                        agg_results,
                        opt_routes_with_hazard,
                    ) = analyzer.multi_link_origin_closest_destination()
                    opt_routes_without_hazard = gpd.GeoDataFrame()

                if analysis.save_gpkg:
                    # Save the GeoDataFrames
                    to_save_gdf = [
                        origins,
                        destinations,
                        opt_routes_without_hazard,
                        opt_routes_with_hazard,
                    ]
                    to_save_gdf_names = [
                        "origins",
                        "destinations",
                        "optimal_routes_without_hazard",
                        "optimal_routes_with_hazard",
                    ]
                    _save_gpkg_analysis(base_graph, to_save_gdf, to_save_gdf_names)
                if analysis.save_csv:
                    csv_path = _output_path.joinpath(
                        analysis.name.replace(" ", "_") + "_destinations.csv"
                    )
                    if "geometry" in destinations.columns:
                        del destinations["geometry"]
                    if not csv_path.parent.exists():
                        csv_path.parent.mkdir(parents=True)
                    destinations.to_csv(csv_path, index=False)

                    csv_path = _output_path.joinpath(
                        analysis.name.replace(" ", "_") + "_optimal_routes.csv"
                    )
                    if not opt_routes_without_hazard.empty:
                        del opt_routes_without_hazard["geometry"]
                        opt_routes_without_hazard.to_csv(csv_path, index=False)
                    if not opt_routes_with_hazard.empty:
                        del opt_routes_with_hazard["geometry"]
                        opt_routes_with_hazard.to_csv(csv_path, index=False)

                if (
                    analyzer.config.files["origins_destinations_graph_hazard"]
                    is not None
                ):
                    agg_results.to_excel(
                        _output_path.joinpath(
                            analysis.name.replace(" ", "_") + "_results.xlsx"
                        ),
                        index=False,
                    )
            elif analysis.analysis == "losses":
                if self.graphs["base_network_hazard"] is None:
                    gdf_in = gpd.read_feather(self.config.files["base_network_hazard"])

                losses = Losses(self.config, analysis)
                df = losses.calculate_losses_from_table()
                gdf = gdf_in.merge(df, how="left", on="LinkNr")
            elif analysis.analysis == "multi_link_isolated_locations":
                g = _pickle_reader.read(self.config.files["base_graph_hazard"])
                gdf, df = self.multi_link_isolated_locations(g, analysis)

                df_path = _output_path / (
                    analysis.name.replace(" ", "_") + "_results.csv"
                )
                df.to_csv(df_path, index=False)
            else:
                _error = f"Analysis {analysis.analysis} does not exist in RA2CE. Please choose an existing analysis."
                logging.error(_error)
                raise ValueError(_error)

            if not gdf.empty:
                # Not for all analyses a gdf is created as output.
                if analysis.save_gpkg:
                    gpkg_path = _output_path.joinpath(
                        analysis.name.replace(" ", "_") + ".gpkg"
                    )
                    save_gdf(gdf, gpkg_path)
                    if opt_routes:
                        gpkg_path = _output_path.joinpath(
                            analysis.name.replace(" ", "_") + "_optimal_routes.gpkg"
                        )
                        save_gdf(gdf, gpkg_path)
                if analysis.save_csv:
                    csv_path = _output_path.joinpath(
                        analysis.name.replace(" ", "_") + ".csv"
                    )
                    gdf.to_csv(csv_path, index=False)

            # Save the configuration for this analysis to the output folder.
            with open(_output_path / "settings.txt", "w") as f:
                for key in analysis.__dict__:
                    print(key + " = " + str(getattr(analysis, key)), file=f)

            endtime = time.time()
            logging.info(
                f"----------------------------- Analysis '{analysis.name}' finished. Time: {str(round(endtime - starttime, 2))}s  -----------------------------"
            )


def save_gdf(gdf: gpd.GeoDataFrame, save_path: Path):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        save_path [str]: output path including extension for edges shapefile
    Returns:
        None
    """
    # save to shapefile
    gdf.crs = "epsg:4326"  # TODO: decide if this should be variable with e.g. an output_crs configured

    for col in gdf.columns:
        if gdf[col].dtype == object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    if save_path.exists():
        save_path.unlink()
    gdf.to_file(save_path, driver="GPKG")
    logging.info("Results saved to: {}".format(save_path))


def find_route_ods(
    graph: nx.classes.MultiGraph,
    od_nodes: list[tuple[tuple[int, str], tuple[int, str]]],
    weighing: str,
) -> gpd.GeoDataFrame:
    # create the routes between all OD pairs
    (
        o_node_list,
        d_node_list,
        origin_list,
        destination_list,
        opt_path_list,
        weighing_list,
        match_ids_list,
        geometries_list,
    ) = ([], [], [], [], [], [], [], [])
    for o, d in tqdm(od_nodes, desc="Finding optimal routes."):
        if nx.has_path(graph, o[0], d[0]):
            # calculate the length of the preferred route
            pref_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=weighing)

            # save preferred route nodes
            pref_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=weighing)

            # found out which edges belong to the preferred path
            edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

            pref_edges = []
            match_list = []
            for u, v in edgesinpath:
                # get edge with the lowest weighing if there are multiple edges that connect u and v
                _uv_graph = graph[u][v]
                edge_key = sorted(
                    _uv_graph, key=lambda x, _fgraph=_uv_graph: _fgraph[x][weighing]
                )[0]
                _uv_graph_edge = _uv_graph[edge_key]
                if "geometry" in _uv_graph_edge:
                    pref_edges.append(_uv_graph_edge["geometry"])
                else:
                    pref_edges.append(
                        LineString(
                            [graph.nodes[u]["geometry"], graph.nodes[v]["geometry"]]
                        )
                    )
                if "rfid" in _uv_graph_edge:
                    match_list.append(_uv_graph_edge["rfid"])

            combined_pref_edges = MultiLineString([])
            for geometry in pref_edges:
                combined_pref_edges = combined_pref_edges.union(geometry)

            if not combined_pref_edges.is_valid:
                print(combined_pref_edges.is_valid)
                print(o[0], d[0])

            # save all data to lists (of lists)
            o_node_list.append(o[0])
            d_node_list.append(d[0])
            origin_list.append(o[1])
            destination_list.append(d[1])
            opt_path_list.append(pref_nodes)
            weighing_list.append(pref_route)
            match_ids_list.append(match_list)
            geometries_list.append(combined_pref_edges)
            # geometries_list.append(pref_edges)

    # Geodataframe to save all the optimal routes
    pref_routes = gpd.GeoDataFrame(
        {
            "o_node": o_node_list,
            "d_node": d_node_list,
            "origin": origin_list,
            "destination": destination_list,
            "opt_path": opt_path_list,
            weighing: weighing_list,
            "match_ids": match_ids_list,
            "geometry": geometries_list,
        },
        geometry="geometry",
        crs="epsg:4326",
    )
    # Remove potential duplicates (o, d node) with a different Origin name.
    _duplicate_columns = ["o_node", "d_node", "destination", "length", "geometry"]
    pref_routes = pref_routes.drop_duplicates(
        subset=_duplicate_columns, keep="first"
    ).reset_index(drop=True)
    return pref_routes


def utm_crs(bbox):
    """Returns wkt string of nearest UTM projects
    Parameters
    ----------
    bbox : array-like of floats
        (xmin, ymin, xmax, ymax) bounding box in latlon WGS84 (EPSG:4326) coordinates
    Returns
    -------
    crs: pyproj.CRS
        CRS of UTM projection

    FROM HYDROMT: https://github.com/Deltares/hydromt - 10.5281/zenodo.6107669
    """
    left, bottom, right, top = bbox
    x = (left + right) / 2
    y = (top + bottom) / 2
    kwargs = dict(zone=int(np.ceil((x + 180) / 6)))
    # BUGFIX hydroMT v0.3.5: south=False doesn't work only add south=True if y<0
    if y < 0:
        kwargs.update(south=True)
    # BUGFIX hydroMT v0.4.6: add datum
    epsg = CRS(proj="utm", datum="WGS84", ellps="WGS84", **kwargs).to_epsg()
    return CRS.from_epsg(epsg)
