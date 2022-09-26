# -*- coding: utf-8 -*-
"""
Created on 26-7-2021
"""

import copy
import logging
import sys
import time
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx
import pandas as pd
from pyproj import CRS
from shapely.geometry import LineString, MultiLineString
from tqdm import tqdm

# Local modules
from ra2ce.graph.networks_utils import graph_to_shp
from ra2ce.io.readers.graph_pickle_reader import GraphPickleReader


class IndirectAnalyses:
    """Indirect analyses that can be done with NetworkX graphs.

    Attributes:
        config: A dictionary with the configuration details on how to create and adjust the network.
        graphs: A dictionary with one or multiple NetworkX graphs.
    """

    def __init__(self, config, graphs):
        self.config = config
        self.graphs = graphs
        if self.config["output"].joinpath("hazard_names.xlsx").is_file():
            self.hazard_names = pd.read_excel(
                self.config["output"].joinpath("hazard_names.xlsx")
            )
            self.config["hazard_names"] = list(set(self.hazard_names["File name"]))

    def single_link_redundancy(self, graph, analysis):
        """This is the function to analyse roads with a single link disruption and an alternative route.

        Args:
            graph: The NetworkX graph to calculate the single link redundancy on.
            analysis: Dictionary of the configurations for the analysis.
        """
        # TODO adjust to the right names of the RA2CE tool
        # if 'road_usage_data_path' in InputDict:
        #     road_usage_data = pd.read_excel(InputDict['road_usage_data_path'])
        #     road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
        #     aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
        # else:
        #     aadt_names = None
        #     road_usage_data = pd.DataFrame()
        road_usage_data = None  # can be removed if the above is fixed
        aadt_names = None  # can be removed if the above is fixed

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
                    graph, u, v, weight=analysis["weighing"]
                )
                alt_dist_list.append(alt_dist)

                # append alternative route nodes
                alt_nodes = nx.dijkstra_path(graph, u, v)
                alt_nodes_list.append(alt_nodes)

                # calculate the difference in distance
                dif_dist_list.append(alt_dist - data[analysis["weighing"]])

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
        gdf["detour_exist"] = detour_exist_list

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return gdf

    def single_link_losses(self, gdf, analysis):
        """Calculates single link disruption losses.

        Args:
            gdf: The network in GeoDataFrame format.
            analysis: Dictionary of the configurations for the analysis.
        """
        losses_fn = self.config["static"] / "hazard" / analysis["loss_per_distance"]
        losses_df = pd.read_excel(losses_fn, sheet_name="Sheet1")

        if analysis["loss_type"] == "categorized":
            disruption_fn = (
                self.config["static"] / "hazard" / analysis["disruption_per_category"]
            )
            disruption_df = pd.read_excel(disruption_fn, sheet_name="Sheet1")

        if (
            analysis["loss_type"] == "uniform"
        ):  # assume uniform threshold for disruption
            for hz in self.config["hazard_names"]:
                for col in analysis["traffic_cols"].split(","):
                    try:
                        assert gdf[col + "_detour_losses"]
                        assert gdf[col + "_nodetour_losses"]
                    except:
                        gdf[col + "_detour_losses"] = 0
                        gdf[col + "_nodetour_losses"] = 0
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle]  * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[
                        (gdf["detour_exist"] == 1)
                        & (
                            gdf[hz + "_" + analysis["aggregate_wl"]]
                            > analysis["threshold"]
                        ),
                        col + "_detour_losses",
                    ] += (
                        gdf[col]
                        * gdf["diff_dist"]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "cost"
                        ].values[0]
                        * analysis["uniform_duration"]
                        / 24
                    )
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita_per_day[USD/person] * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[
                        (gdf["detour_exist"] == 0)
                        & (
                            gdf[hz + "_" + analysis["aggregate_wl"]]
                            > analysis["threshold"]
                        ),
                        col + "_nodetour_losses",
                    ] += (
                        gdf[col]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "occupancy"
                        ].values[0]
                        * analysis["gdp_percapita"]
                        * analysis["uniform_duration"]
                        / 24
                    )
                gdf["total_losses_" + hz] = np.nansum(
                    gdf[
                        [
                            x
                            for x in gdf.columns
                            if ("losses" in x) and (not "total" in x)
                        ]
                    ],
                    axis=1,
                )

        if analysis["loss_type"] == "categorized":
            road_classes = [x for x in disruption_df.columns if "class" in x]
            for hz in self.config["hazard_names"]:
                disruption_df["class_identifier"] = ""
                gdf["class_identifier"] = ""
                for i, road_class in enumerate(road_classes):
                    disruption_df["class_identifier"] += disruption_df[road_class]
                    gdf["class_identifier"] += gdf[road_class[6:]]
                    if i < len(road_classes) - 1:
                        disruption_df["class_identifier"] += "_nextclass_"
                        gdf["class_identifier"] += "_nextclass_"

                all_road_categories = np.unique(gdf["class_identifier"])
                gdf["duration_disruption"] = 0

                for lb in np.unique(disruption_df["lower_bound"]):
                    disruption_df_ = disruption_df.loc[
                        disruption_df["lower_bound"] == lb
                    ]
                    ub = disruption_df_["upper_bound"].values[0]
                    if not ub > 0:
                        ub = 1e10
                    for road_cat in all_road_categories:
                        gdf.loc[
                            (gdf[hz + "_" + analysis["aggregate_wl"]] > lb)
                            & (gdf[hz + "_" + analysis["aggregate_wl"]] <= ub)
                            & (gdf["class_identifier"] == road_cat),
                            "duration_disruption",
                        ] = disruption_df_.loc[
                            disruption_df_["class_identifier"] == road_cat,
                            "duration_disruption",
                        ].values[
                            0
                        ]

                for col in analysis["traffic_cols"].split(","):
                    try:
                        assert gdf[col + "_detour_losses"]
                        assert gdf[col + "_nodetour_losses"]
                    except:
                        gdf[col + "_detour_losses"] = 0
                        gdf[col + "_nodetour_losses"] = 0
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[gdf["detour_exist"] == 1, col + "_detour_losses"] += (
                        gdf[col]
                        * gdf["diff_dist"]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "cost"
                        ].values[0]
                        * gdf["duration_disruption"]
                        / 24
                    )
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita[USD/person] * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[gdf["detour_exist"] == 0, col + "_nodetour_losses"] += (
                        gdf[col]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "occupancy"
                        ].values[0]
                        * analysis["gdp_percapita"]
                        * gdf["duration_disruption"]
                        / 24
                    )
                gdf["total_losses_" + hz] = np.nansum(
                    gdf[
                        [
                            x
                            for x in gdf.columns
                            if ("losses" in x) and (not "total" in x)
                        ]
                    ],
                    axis=1,
                )

        return gdf

    def multi_link_redundancy(self, graph, analysis):
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
        for hazard in self.config["hazard_names"]:
            hazard_name = self.hazard_names.loc[
                self.hazard_names["File name"] == hazard, "RA2CE name"
            ].values[0]

            graph = copy.deepcopy(master_graph)
            # Create a geodataframe from the full graph
            gdf = osmnx.graph_to_gdfs(master_graph, nodes=False)
            gdf["rfid"] = gdf["rfid"].astype(str)

            # Create the edgelist that consist of edges that should be removed
            edges_remove = [
                e for e in graph.edges.data(keys=True) if hazard_name in e[-1]
            ]
            edges_remove = [e for e in edges_remove if (e[-1][hazard_name] is not None)]
            edges_remove = [
                e
                for e in edges_remove
                if (e[-1][hazard_name] > float(analysis["threshold"]))
                & ("bridge" not in e[-1])
            ]

            graph.remove_edges_from(edges_remove)

            # dataframe for saving the calculations of the alternative routes
            df_calculated = pd.DataFrame(
                columns=["u", "v", "rfid", "alt_dist", "alt_nodes", "connected"]
            )

            for i, edges in enumerate(edges_remove):
                u, v, k, edata = edges

                # check if the nodes are still connected
                if nx.has_path(graph, u, v):
                    # calculate the alternative distance if that edge is unavailable
                    alt_dist = nx.dijkstra_path_length(
                        graph, u, v, weight=analysis["weighing"]
                    )

                    # save alternative route nodes
                    alt_nodes = nx.dijkstra_path(graph, u, v)

                    # append to calculation dataframe
                    df_calculated = df_calculated.append(
                        {
                            "u": u,
                            "v": v,
                            "rfid": str(edata["rfid"]),
                            "alt_dist": alt_dist,
                            "alt_nodes": alt_nodes,
                            "connected": 1,
                        },
                        ignore_index=True,
                    )
                else:
                    # append to calculation dataframe
                    df_calculated = df_calculated.append(
                        {
                            "u": u,
                            "v": v,
                            "rfid": str(edata["rfid"]),
                            "alt_dist": np.NaN,
                            "alt_nodes": np.NaN,
                            "connected": 0,
                        },
                        ignore_index=True,
                    )

            # Merge the dataframes
            gdf = gdf.merge(df_calculated, how="left", on=["u", "v", "rfid"])

            # calculate the difference in distance
            # previously here you would find if dist == dist which is a critical bug. Replaced by just verifying dist is a value.
            gdf["diff_dist"] = [
                dist - length if dist else np.NaN
                for (dist, length) in zip(gdf["alt_dist"], gdf[analysis["weighing"]])
            ]

            gdf["hazard"] = hazard_name

            results.append(gdf)

        aggregated_results = pd.concat(results, ignore_index=True)
        return aggregated_results

    def multi_link_losses(self, gdf, analysis):
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
        losses_fn = self.config["static"] / "hazard" / analysis["loss_per_distance"]
        losses_df = pd.read_excel(losses_fn, sheet_name="Sheet1")

        if analysis["loss_type"] == "categorized":
            disruption_fn = (
                self.config["static"] / "hazard" / analysis["disruption_per_category"]
            )
            disruption_df = pd.read_excel(disruption_fn, sheet_name="Sheet1")
            road_classes = [x for x in disruption_df.columns if "class" in x]

        results = []
        for hazard in self.config["hazard_names"]:
            hazard_name = self.hazard_names.loc[
                self.hazard_names["File name"] == hazard, "RA2CE name"
            ].values[0]

            gdf_ = gdf.loc[gdf["hazard"] == hazard_name].copy()
            if (
                analysis["loss_type"] == "uniform"
            ):  # assume uniform threshold for disruption
                for col in analysis["traffic_cols"].split(","):
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    gdf_.loc[gdf_["connected"] == 1, col + "_losses_detour"] = (
                        gdf_[col]
                        * gdf_["diff_dist"]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "cost"
                        ].values[0]
                        * analysis["uniform_duration"]
                        / 24
                    )
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy_per_vehicle[person/veh] * duration_disruption[hour] / 24[hour/day] * gdp_percapita_per_day [USD/person]
                    gdf_.loc[gdf_["connected"] == 0, col + "_losses_nodetour"] = (
                        gdf_[col]
                        * losses_df.loc[
                            losses_df["traffic_class"] == col, "occupancy"
                        ].values[0]
                        * analysis["gdp_percapita"]
                        * analysis["uniform_duration"]
                        / 24
                    )
                gdf_["total_losses_" + hz] = np.nansum(
                    gdf_[
                        [
                            x
                            for x in gdf_.columns
                            if ("losses" in x) and (not "total" in x)
                        ]
                    ],
                    axis=1,
                )

            if (
                analysis["loss_type"] == "categorized"
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
                    if not ub > 0:
                        ub = 1e10
                    for road_cat in all_road_categories:
                        gdf_.loc[
                            (gdf_[hz + "_" + analysis["aggregate_wl"]] > lb)
                            & (gdf_[hz + "_" + analysis["aggregate_wl"]] <= ub)
                            & (gdf_["class_identifier"] == road_cat),
                            "duration_disruption",
                        ] = disruption_df_.loc[
                            disruption_df_["class_identifier"] == road_cat,
                            "duration_disruption",
                        ].values[
                            0
                        ]

                for col in analysis["traffic_cols"].split(","):
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
                        * analysis["gdp_percapita"]
                        * gdf_["duration_disruption"]
                        / 24
                    )
                gdf_["total_losses_" + hz] = np.nansum(
                    gdf_[
                        [
                            x
                            for x in gdf_.columns
                            if ("losses" in x) and (not "total" in x)
                        ]
                    ],
                    axis=1,
                )
            results.append(gdf_)

        aggregated_results = pd.concat(results, ignore_index=True)
        return aggregated_results

    def optimal_route_origin_destination(self, graph, analysis):
        # Calculate the preferred routes
        name = analysis["name"].replace(" ", "_")

        # create list of origin-destination pairs
        od_path = (
            self.config["static"] / "output_graph" / "origin_destination_table.feather"
        )
        od = gpd.read_feather(od_path)
        od_pairs = [
            (a, b)
            for a in od.loc[od["o_id"].notnull(), "o_id"]
            for b in od.loc[od["d_id"].notnull(), "d_id"]
        ]
        all_nodes = [(n, v["od_id"]) for n, v in graph.nodes(data=True) if "od_id" in v]
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

        pref_routes = find_route_ods(graph, od_nodes, analysis["weighing"])

        # if shortest_route:
        #     pref_routes = pref_routes.loc[pref_routes.sort_values(analysis['weighing']).groupby('o_node').head(3).index]
        return pref_routes

    def optimal_route_od_link(self, gdf, od_table, equity):
        origin_nodes = np.unique(gdf["origin"])
        destination_nodes = np.unique(gdf["destination"])

        unique_destination_nodes = np.unique(list(od_table["d_id"].fillna("0")))
        count_destination_nodes = len([x for x in unique_destination_nodes if x != "0"])

        route_traffic = {}
        route_traffic_equal = {}
        if len(equity) > 0:
            route_traffic_prioritarian = {}
            prioritarian_mapping = dict(zip(equity["region"], equity["weight"]))
            prioritarian_mapping.update({"Not assigned": 1})
            od_table["values_prioritarian"] = (
                od_table["region"].map(prioritarian_mapping) * od_table["values"]
            )
        for o_node in origin_nodes:
            for d_node in destination_nodes:
                opt_path = gdf.loc[
                    (gdf["origin"] == o_node) & (gdf["destination"] == d_node),
                    "opt_path",
                ].values[0]
                for i, node in enumerate(range(len(opt_path))):
                    if i < len(opt_path) - 1:
                        u, v = opt_path[i], opt_path[i + 1]
                        t = 1
                        t_eq = 1
                        if len(equity) > 0:
                            t_prioritarian = 1
                        if "," in o_node:
                            o_nodes = o_node.split(",")
                            o_num = len(o_nodes)
                            j_ = 0
                            for j, o_n in enumerate(o_nodes):
                                if (
                                    self.config["origins_destinations"][
                                        "destinations_names"
                                    ]
                                    in o_n
                                ):
                                    o_num -= 1
                                    j_ -= 1
                                    continue
                                else:
                                    traffic = (
                                        od_table.loc[
                                            od_table["o_id"] == o_n, "values"
                                        ].values[0]
                                        / count_destination_nodes
                                    )
                                if j_ == 0:
                                    t *= traffic
                                else:
                                    t += traffic
                                if len(equity) > 0:
                                    traffic_prioritarian = (
                                        od_table.loc[
                                            od_table["o_id"] == o_n,
                                            "values_prioritarian",
                                        ].values[0]
                                        / count_destination_nodes
                                    )
                                    if j_ == 0:
                                        t_prioritarian *= traffic_prioritarian
                                    else:
                                        t_prioritarian += traffic_prioritarian
                                j_ += 1
                            t_eq *= o_num
                        else:
                            traffic = (
                                od_table.loc[
                                    od_table["o_id"] == o_node, "values"
                                ].values[0]
                                / count_destination_nodes
                            )
                            t *= traffic
                            if len(equity) > 0:
                                traffic_prioritarian = (
                                    od_table.loc[
                                        od_table["o_id"] == o_node,
                                        "values_prioritarian",
                                    ].values[0]
                                    / count_destination_nodes
                                )
                                t_prioritarian *= traffic_prioritarian
                        if "," in d_node:
                            d_nodes = d_node.split(",")
                            d_num = len(d_nodes)
                            t_eq *= d_num
                            t *= d_num
                            if len(equity) > 0:
                                t_prioritarian *= d_num
                        try:
                            route_traffic[str(u) + "_" + str(v)] += t
                            route_traffic_equal[str(u) + "_" + str(v)] += t_eq
                            if len(equity) > 0:
                                route_traffic_prioritarian[
                                    str(u) + "_" + str(v)
                                ] += t_prioritarian
                        except:
                            route_traffic.update({str(u) + "_" + str(v): t})
                            route_traffic_equal.update({str(u) + "_" + str(v): t_eq})
                            if len(equity) > 0:
                                route_traffic_prioritarian.update(
                                    {str(u) + "_" + str(v): t_prioritarian}
                                )

        u_list = [x.split("_")[0] for x in route_traffic.keys()]
        v_list = [x.split("_")[1] for x in route_traffic.keys()]
        t_list = route_traffic.values()
        teq_list = route_traffic_equal.values()
        if len(equity) > 0:
            tprioritarian_list = route_traffic_prioritarian.values()
            data_tuples = list(
                zip(u_list, v_list, t_list, teq_list, tprioritarian_list)
            )
            route_traffic_df = pd.DataFrame(
                data_tuples,
                columns=[
                    "u",
                    "v",
                    "traffic",
                    "traffic_egalitarian",
                    "traffic_prioritarian",
                ],
            )
        else:
            data_tuples = list(zip(u_list, v_list, t_list, teq_list))
            route_traffic_df = pd.DataFrame(
                data_tuples, columns=["u", "v", "traffic", "traffic_egalitarian"]
            )

        return route_traffic_df

    def multi_link_origin_destination(self, graph, analysis):
        """Calculates the connectivity between origins and destinations"""
        # create list of origin-destination pairs
        od_path = (
            self.config["static"] / "output_graph" / "origin_destination_table.feather"
        )
        od = gpd.read_feather(od_path)
        od_pairs = [
            (a, b)
            for a in od.loc[od["o_id"].notnull(), "o_id"]
            for b in od.loc[od["d_id"].notnull(), "d_id"]
        ]
        all_nodes = [(n, v["od_id"]) for n, v in graph.nodes(data=True) if "od_id" in v]
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

        all_results = []
        for hazard in self.config["hazard_names"]:
            hazard_name = self.hazard_names.loc[
                self.hazard_names["File name"] == hazard, "RA2CE name"
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
                if (e[-1][hazard_name] > float(analysis["threshold"]))
                & ("bridge" not in e[-1])
            ]
            graph_hz.remove_edges_from(edges_remove)

            # Find the routes
            od_routes = find_route_ods(graph_hz, od_nodes, analysis["weighing"])
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
        init_origins = gdf_ori.groupby("origin").mean()["origin_count"].sum()
        del gdf_ori["origin_count"]
        # destination
        gdf_ori["destination_count"] = gdf_ori["destination"].apply(
            lambda x: len(x.split(","))
        )
        init_destinations = (
            gdf_ori.groupby("destination").mean()["destination_count"].sum()
        )
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
            remaining_origins = gdf_.groupby("origin").mean()["origin_count"].sum()
            del gdf_["origin_count"]
            diff_origins = init_origins - remaining_origins
            abs_origin_disconnected.append(diff_origins)
            share_origin_disconnected.append(100 * diff_origins / init_origins)

            gdf_["destination_count"] = gdf_["destination"].apply(
                lambda x: len(x.split(","))
            )
            remaining_destinations = (
                gdf_.groupby("destination").mean()["destination_count"].sum()
            )
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
        origin_fn = (
            Path(self.config["static"])
            / "output_graph"
            / "origin_destination_table.shp"
        )
        origin = gpd.read_file(origin_fn)
        index = [type(x) == str for x in origin["o_id"]]
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
                        if not delta >= 0:
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

    def optimal_route_origin_closest_destination(self, graph, analysis):
        crs = 4326  # TODO PUT IN DOCUMENTATION OR MAKE CHANGABLE

        base_graph = copy.deepcopy(graph)
        nx.set_edge_attributes(base_graph, 0, "opt_cnt")

        o_name = self.config["origins_destinations"]["origins_names"]
        d_name = self.config["origins_destinations"]["destinations_names"]
        od_id = self.config["origins_destinations"]["id_name_origin_destination"]
        id_name = (
            self.config["network"]["file_id"]
            if self.config["network"]["file_id"] is not None
            else "rfid"
        )
        count_col_name = self.config["origins_destinations"]["origin_count"]
        weight_factor = self.config["origins_destinations"]["origin_out_fraction"]

        origin = load_origins(self.config)

        origin_closest_dest, other = find_closest_node_attr(
            graph, "od_id", analysis["weighing"], o_name, d_name
        )
        pref_routes, base_graph = calc_pref_routes_closest_dest(
            graph,
            base_graph,
            analysis["weighing"],
            crs,
            od_id,
            id_name,
            origin_closest_dest,
            origin,
            count_col_name,
            weight_factor,
        )

        destinations = load_destinations(self.config)

        cnt_per_destination = (
            pref_routes.groupby("destination")[["origin_cnt", "cnt_weight"]]
            .sum()
            .reset_index()
        )
        for hosp, origin_cnt, cnt_weight in zip(
            cnt_per_destination["destination"],
            cnt_per_destination["origin_cnt"],
            cnt_per_destination["cnt_weight"],
        ):
            destinations.loc[
                destinations[od_id] == int(hosp.split("_")[-1]), "origin_cnt"
            ] = origin_cnt
            destinations.loc[
                destinations[od_id] == int(hosp.split("_")[-1]), "cnt_weight"
            ] = cnt_weight

        return base_graph, pref_routes, destinations

    def multi_link_origin_closest_destination(
        self, graph, base_graph, destinations, analysis, opt_routes
    ):
        unit = "km"
        network_threshold = analysis["threshold"]
        weighing = analysis["weighing"]
        od_id = self.config["origins_destinations"]["id_name_origin_destination"]
        o_name = self.config["origins_destinations"]["origins_names"]
        d_name = self.config["origins_destinations"]["destinations_names"]
        origin_out_fraction = self.config["origins_destinations"]["origin_out_fraction"]
        origin_count = self.config["origins_destinations"]["origin_count"]

        aggregated = pd.DataFrame(
            columns=[
                "Flood map",
                "Nr. people no delay",
                "Nr. people delayed",
                "Nr. people no access",
                "Total extra detour time (hours)",
                f"Total extra detour distance ({unit})",
                "Disruption by flooded road",
                "Disruption by flooded destination",
            ]
        )

        origins = load_origins(self.config)
        threshold_destinations = 0

        # Calculate the criticality
        for hazard in self.config["hazard_names"]:
            hazard_name_short = self.hazard_names.loc[
                self.hazard_names["File name"] == hazard, "RA2CE name"
            ].values[0][:-3]
            hazard_name = self.hazard_names.loc[
                self.hazard_names["File name"] == hazard, "RA2CE name"
            ].values[0]

            # Add a column for the number of people that go to a certain destination, per flood map
            destinations[hazard_name_short + "_P"] = 0
            nx.set_edge_attributes(base_graph, 0, hazard_name_short + "_P")

            # Add a column to the neighborhoods, to indicate if they have access to any hospital
            origins[hazard_name_short + "_NA"] = "access"

            # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
            h = copy.deepcopy(graph)

            edges_remove = [
                e for e in graph.edges.data(keys=True) if hazard_name in e[-1]
            ]
            edges_remove = [e for e in edges_remove if (e[-1][hazard_name] is not None)]
            edges_remove = [
                e
                for e in edges_remove
                if (e[-1][hazard_name] > float(analysis["threshold"]))
                & ("bridge" not in e[-1])
            ]
            h.remove_edges_from(edges_remove)

            # Find the closest hospitals
            list_closest, other = find_closest_node_attr(
                h, "od_id", weighing, o_name, d_name
            )

            # Find the distance of the routes to the hospitals, see if those hospitals are flooded or not
            (
                base_graph,
                destinations,
                list_disrupted_dest,
                pp_no_delay,
                pp_delayed,
                extra_dist_meters,
                extra_miles,
            ) = calc_routes_closest_dest(
                h,
                base_graph,
                list_closest,
                opt_routes,
                weighing,
                origins,
                destinations,
                od_id,
                hazard_name,
                threshold_destinations,
                origin_out_fraction,
                origin_count,
            )

            # Calculate the number of people that cannot access any hospital
            pp_no_access = [
                origins.loc[
                    origins[od_id] == int(oth[1].split("_")[-1]), origin_count
                ].iloc[0]
                * origin_out_fraction
                if len(other) > 0
                else 0
                for oth in other
            ]

            # Attribute to the neighborhoods that don't have access that they do not have any access
            if len(other) > 0:
                for oth in other:
                    origins.loc[
                        origins[od_id] == int(oth[1].split("_")[-1]),
                        hazard_name + "_NA",
                    ] = "no access"

            # Now calculate for the routes that were going to a flooded destination, another non-flooded destination
            # TODO THIS PART NEEDS TO BE CHECKED AND REVISED >>>
            list_dests_flooded = [dest[-1][-1] for dest in list_disrupted_dest]

            disr_by_flood = 0

            if len(list_dests_flooded) > 0:
                list_nodes_to_remove = [n for n in h.nodes.data() if "od_id" in n[-1]]
                list_nodes_to_remove = [
                    n[0]
                    for n in list_nodes_to_remove
                    if n[-1]["od_id"] in list_disrupted_dest
                ]
                graph.remove_nodes_from(list_nodes_to_remove)

                disr_by_flood = 1
                list_closest, other = find_closest_node_attr(
                    h, "od_id", weighing, o_name, d_name
                )

            # The number of people that are disrupted because of a flooded road (and not because the or multiple destinations are disrupted)
            # can be calculated by adding the people without any access (this is always because of flooded roads in the first place)
            # and the people that are delayed. By subtracting the people that are disrupted by hospitals you get only the people
            # disrupted by road flooding.
            disr_by_flooded_road = (
                round(sum(pp_no_access)) + round(sum(pp_delayed)) - disr_by_flood
            )
            # TODO THIS PART NEEDS TO BE CHECKED AND REVISED <<<

            aggregated = aggregated.append(
                {
                    "Flood map": hazard_name,
                    "Nr. people no delay": round(sum(pp_no_delay)),
                    "Nr. people delayed": round(sum(pp_delayed)),
                    "Nr. people no access": round(sum(pp_no_access)),
                    "Total extra detour time (hours)": sum(extra_dist_meters),
                    f"Total extra detour distance ({unit})": sum(extra_miles),
                    "Disruption by flooded road": disr_by_flooded_road,
                    "Disruption by flooded destination": disr_by_flood,
                },
                ignore_index=True,
            )

        return base_graph, origins, destinations, aggregated

    def multi_link_isolated_locations(self, graph, analysis, crs=4326):
        # TODO PUT CRS IN DOCUMENTATION OR MAKE CHANGABLE

        # Load the point shapefile with the locations of which the isolated locations should be identified.
        locations = gpd.read_feather(
            self.config["static"] / "output_graph" / "locations_hazard.feather"
        )

        # reproject the datasets to be able to make a buffer in meters
        nearest_utm = utm_crs(locations.total_bounds)
        locations = locations.set_crs(epsg=crs)
        locations.to_crs(crs=nearest_utm, inplace=True)

        isolated_locations = copy.deepcopy(locations)

        for i, hazard in enumerate(self.config["hazard_names"]):
            hazard_name = self.hazard_names.loc[
                self.hazard_names["File name"] == hazard, "RA2CE name"
            ].values[0]

            graph_hz = copy.deepcopy(graph)

            # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
            edges_remove = [
                e for e in graph.edges.data(keys=True) if hazard_name in e[-1]
            ]
            edges_remove = [
                e
                for e in edges_remove
                if (e[-1][hazard_name] > float(analysis["threshold"]))
                & ("bridge" not in e[-1])
            ]
            graph_hz.remove_edges_from(edges_remove)

            # evaluate on connected components
            connected_components = list(
                graph_hz.subgraph(c) for c in nx.connected_components(graph_hz)
            )

            # find the disconnected islands and merge their linestrings into one multilinestring
            # save the geometries in a geodataframe where later the isolated are counted in
            results = gpd.GeoDataFrame(
                columns=["fid", "count", "geometry"], geometry="geometry", crs=crs
            )
            for ii, g in enumerate(connected_components):
                if g.size() == 0:
                    continue
                edges_geoms = []
                count_edges = 0
                for edge in g.edges(data=True):
                    edges_geoms.append(edge[-1]["geometry"])
                    count_edges += 1
                total_geom = MultiLineString(edges_geoms)
                results = results.append(
                    {"fid": ii, "count": count_edges, "geometry": total_geom},
                    ignore_index=True,
                )

            # remove the largest (main) graph
            results.sort_values(by="count", ascending=False, inplace=True)
            results = results.loc[results["count"] != results["count"].max()]

            # reproject the datasets to be able to make a buffer in meters
            results = results.set_crs(crs=crs)
            results.to_crs(crs=nearest_utm, inplace=True)

            results_buffered = results.copy()
            results_buffered.geometry = results_buffered.geometry.buffer(
                analysis["buffer_meters"]
            )
            results_buffered.to_file(
                self.config["output"]
                / analysis["analysis"]
                / f"isolated_{hazard_name}.shp"
            )  # Save the buffer

            intersect = gpd.overlay(results_buffered, locations, keep_geom_type=False)
            intersect.set_crs(crs=nearest_utm)

            # Replace nan with 0 for the water depth columns
            intersect[hazard_name] = intersect[hazard_name].fillna(0)

            # TODO: Put in analyses.ini file a variable to set the threshold for locations that are not isolated when they are flooded.
            # Extract the flood depth of the locations
            # intersect = intersect.loc[intersect[hazard_name] > analysis['threshold_locations']]

            # Save the results in isolated_locations
            isolated_locations[f"i_{hazard_name[:-3]}"] = [
                1 if idx in intersect["i_id"] else 0
                for idx in isolated_locations["i_id"]
            ]

            # Group by commercial category and count the number of businesses per category
            if i == 0:
                # the first iteration, create a new pd dataframe
                df_aggregation = (
                    intersect.groupby(analysis["category_field_name"])
                    .size()
                    .to_frame(hazard_name)
                )
            else:
                # after more iterations the new columns are appended
                df_aggregation = df_aggregation.join(
                    intersect.groupby(analysis["category_field_name"])
                    .size()
                    .to_frame(hazard_name),
                    how="outer",
                )

        # Wide to long format for the aggregated results
        df_aggregation = pd.melt(df_aggregation)
        df_aggregation.rename(
            columns={"variable": "Hazard", "value": "Nr. isolated"}, inplace=True
        )

        # Set the isolated_locations geopandas dataframe back to the original crs
        isolated_locations.to_crs(crs=crs, inplace=True)
        return isolated_locations, df_aggregation

    def execute(self):
        """Executes the indirect analysis."""
        _pickle_reader = GraphPickleReader()
        for analysis in self.config["indirect"]:
            logging.info(
                f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------"
            )
            starttime = time.time()
            gdf = pd.DataFrame()
            opt_routes = None
            output_path = self.config["output"] / analysis["analysis"]

            if "weighing" in analysis:
                if analysis["weighing"] == "distance":
                    # The name is different in the graph.
                    analysis["weighing"] = "length"
            _config_files = self.config["files"]
            if analysis["analysis"] == "single_link_redundancy":
                g = _pickle_reader.read(_config_files["base_graph"])
                gdf = self.single_link_redundancy(g, analysis)
            elif analysis["analysis"] == "multi_link_redundancy":
                g = _pickle_reader.read(_config_files["base_graph_hazard"])
                gdf = self.multi_link_redundancy(g, analysis)
            elif analysis["analysis"] == "optimal_route_origin_destination":
                g = _pickle_reader.read(_config_files["origins_destinations_graph"])
                gdf = self.optimal_route_origin_destination(g, analysis)

                if ("save_traffic" in analysis.keys()) & (
                    "origin_count" in self.config["origins_destinations"].keys()
                ):
                    if analysis["save_traffic"]:
                        od_table = gpd.read_feather(
                            self.config["static"]
                            / "output_graph"
                            / "origin_destination_table.feather"
                        )
                        if "equity_weight" in analysis.keys():
                            try:
                                equity = pd.read_csv(
                                    self.config["static"]
                                    / "network"
                                    / analysis["equity_weight"]
                                )
                            except:
                                equity = pd.DataFrame()
                        else:
                            equity = pd.DataFrame()
                        route_traffic_df = self.optimal_route_od_link(
                            gdf, od_table, equity
                        )
                        impact_csv_path = (
                            self.config["output"]
                            / analysis["analysis"]
                            / (analysis["name"].replace(" ", "_") + "_link_traffic.csv")
                        )
                        route_traffic_df.to_csv(impact_csv_path, index=False)

            elif analysis["analysis"] == "multi_link_origin_destination":
                g = _pickle_reader.read(
                    self.config["files"]["origins_destinations_graph_hazard"]
                )
                gdf = self.multi_link_origin_destination(g, analysis)
                g_not_disrupted = _pickle_reader.read(
                    self.config["files"]["origins_destinations_graph_hazard"]
                )
                gdf_not_disrupted = self.optimal_route_origin_destination(
                    g_not_disrupted, analysis
                )
                (
                    disruption_impact_df,
                    gdf_ori,
                ) = self.multi_link_origin_destination_impact(gdf, gdf_not_disrupted)
                try:
                    assert self.config["origins_destinations"]["region"]
                    (
                        regional_impact_df,
                        regional_impact_summary_df,
                    ) = self.multi_link_origin_destination_regional_impact(gdf_ori)
                    impact_csv_path = (
                        self.config["output"]
                        / analysis["analysis"]
                        / (analysis["name"].replace(" ", "_") + "_regional_impact.csv")
                    )
                    regional_impact_df.to_csv(impact_csv_path, index=False)
                    impact_csv_path = (
                        self.config["output"]
                        / analysis["analysis"]
                        / (
                            analysis["name"].replace(" ", "_")
                            + "_regional_impact_summary.csv"
                        )
                    )
                    regional_impact_summary_df.to_csv(impact_csv_path)
                except:
                    pass
                impact_csv_path = (
                    self.config["output"]
                    / analysis["analysis"]
                    / (analysis["name"].replace(" ", "_") + "_impact.csv")
                )
                del gdf_ori["geometry"]
                gdf_ori.to_csv(impact_csv_path, index=False)
                impact_csv_path = (
                    self.config["output"]
                    / analysis["analysis"]
                    / (analysis["name"].replace(" ", "_") + "_impact_summary.csv")
                )
                disruption_impact_df.to_csv(impact_csv_path, index=False)
            elif analysis["analysis"] == "single_link_losses":
                g = _pickle_reader.read(self.config["files"]["base_graph_hazard"])
                gdf = self.single_link_redundancy(g, analysis)
                gdf = self.single_link_losses(gdf, analysis)
            elif analysis["analysis"] == "multi_link_losses":
                g = _pickle_reader.read(self.config["files"]["base_graph_hazard"])
                gdf = self.multi_link_redundancy(g, analysis)
                gdf = self.multi_link_losses(gdf, analysis)
            elif analysis["analysis"] == "optimal_route_origin_closest_destination":
                g = _pickle_reader.read(
                    self.config["files"]["origins_destinations_graph"]
                )
                (
                    base_graph,
                    opt_routes,
                    destination,
                ) = self.optimal_route_origin_closest_destination(g, analysis)
                if analysis["save_shp"]:
                    # TODO MAKE ONE GDF FROM RESULTS?
                    shp_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_destinations.shp"
                    )
                    save_gdf(destination, shp_path)

                    shp_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_optimal_routes.shp"
                    )
                    save_gdf(opt_routes, shp_path)

                    shp_path_nodes = output_path / (
                        analysis["name"].replace(" ", "_") + "_results_nodes.shp"
                    )
                    shp_path_edges = output_path / (
                        analysis["name"].replace(" ", "_") + "_results_edges.shp"
                    )
                    graph_to_shp(base_graph, shp_path_edges, shp_path_nodes)
                if analysis["save_csv"]:
                    csv_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_destinations.csv"
                    )
                    del destination["geometry"]
                    destination.to_csv(csv_path, index=False)

                    csv_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_optimal_routes.csv"
                    )
                    del opt_routes["geometry"]
                    opt_routes.to_csv(csv_path, index=False)
            elif analysis["analysis"] == "multi_link_origin_closest_destination":
                # TODO MAKE ONE GDF FROM RESULTS?
                g = _pickle_reader.read(
                    self.config["files"]["origins_destinations_graph_hazard"]
                )
                (
                    base_graph,
                    opt_routes,
                    destinations,
                ) = self.optimal_route_origin_closest_destination(g, analysis)

                (
                    base_graph,
                    origins,
                    destinations,
                    agg_results,
                ) = self.multi_link_origin_closest_destination(
                    g, base_graph, destinations, analysis, opt_routes
                )
                if analysis["save_shp"]:
                    shp_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_origins.shp"
                    )
                    save_gdf(origins, shp_path)

                    shp_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_destinations.shp"
                    )
                    save_gdf(destinations, shp_path)

                    shp_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_optimal_routes.shp"
                    )
                    save_gdf(opt_routes, shp_path)

                    shp_path_nodes = output_path / (
                        analysis["name"].replace(" ", "_") + "_results_nodes.shp"
                    )
                    shp_path_edges = output_path / (
                        analysis["name"].replace(" ", "_") + "_results_edges.shp"
                    )
                    graph_to_shp(base_graph, shp_path_edges, shp_path_nodes)
                if analysis["save_csv"]:
                    csv_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_destinations.csv"
                    )
                    if "geometry" in destinations.columns:
                        del destinations["geometry"]
                    destinations.to_csv(csv_path, index=False)

                    csv_path = output_path / (
                        analysis["name"].replace(" ", "_") + "_optimal_routes.csv"
                    )
                    del opt_routes["geometry"]
                    opt_routes.to_csv(csv_path, index=False)

                agg_results.to_excel(
                    output_path
                    / (analysis["name"].replace(" ", "_") + "_results.xlsx"),
                    index=False,
                )

            elif analysis["analysis"] == "losses":

                if self.graphs["base_network_hazard"] is None:
                    gdf_in = gpd.read_feather(
                        self.config["files"]["base_network_hazard"]
                    )

                losses = Losses(self.config, analysis)
                df = losses.calculate_losses_from_table()
                gdf = gdf_in.merge(df, how="left", on="LinkNr")
            elif analysis["analysis"] == "multi_link_isolated_locations":
                g = _pickle_reader.read(self.config["files"]["base_graph_hazard"])
                gdf, df = self.multi_link_isolated_locations(g, analysis)

                df_path = output_path / (
                    analysis["name"].replace(" ", "_") + "_results.csv"
                )
                df.to_csv(df_path, index=False)
            else:
                logging.error(
                    f"Analysis {analysis['analysis']} does not exist in RA2CE. Please choose an existing analysis."
                )
                sys.exit()

            if not gdf.empty:
                # Not for all analyses a gdf is created as output.
                if analysis["save_shp"]:
                    shp_path = output_path / (
                        analysis["name"].replace(" ", "_") + ".shp"
                    )
                    save_gdf(gdf, shp_path)
                    if opt_routes:
                        shp_path = output_path / (
                            analysis["name"].replace(" ", "_") + "_optimal_routes.shp"
                        )
                        save_gdf(gdf, shp_path)
                if analysis["save_csv"]:
                    csv_path = output_path / (
                        analysis["name"].replace(" ", "_") + ".csv"
                    )
                    del gdf["geometry"]
                    gdf.to_csv(csv_path, index=False)

            # Save the configuration for this analysis to the output folder.
            with open(output_path / "settings.txt", "w") as f:
                for key in analysis:
                    print(key + " = " + str(analysis[key]), file=f)

            endtime = time.time()
            logging.info(
                f"----------------------------- Analysis '{analysis['name']}' finished. Time: {str(round(endtime - starttime, 2))}s  -----------------------------"
            )
        return


class Losses:
    def __init__(self, config, analysis):
        self.config = config
        self.analysis = analysis
        self.duration = analysis["duration_event"]
        self.duration_disr = analysis["duration_disruption"]
        self.detour_traffic = analysis["fraction_detour"]
        self.traffic_throughput = analysis["fraction_drivethrough"]
        self.rest_capacity = analysis["rest_capacity"]
        self.maximum = analysis["maximum_jam"]
        self.partofday = analysis["partofday"]

    @staticmethod
    def vehicle_loss_hours(path):
        """This function is to calculate vehicle loss hours based on an input table
        with value of time per type of transport, usage and value_of_reliability"""

        file_path = path / "vehicle_loss_hours.csv"
        df_lookup = pd.read_csv(file_path, index_col="transport_type")
        lookup_dict = df_lookup.transpose().to_dict()
        return lookup_dict

    @staticmethod
    def load_df(path, file):
        """This method reads the dataframe created from a .csv"""
        file_path = path / file
        df = pd.read_csv(file_path, index_col="LinkNr")
        return df

    def traffic_shockwave(self, vlh, capacity, intensity):
        vlh["vlh_traffic"] = (
            (self.duration**2)
            * (self.rest_capacity - 1)
            * (self.rest_capacity * capacity - intensity / self.traffic_throughput)
            / (2 * (1 - ((intensity / self.traffic_throughput) / capacity)))
        )
        return vlh

    def calc_vlh(self, traffic_data, vehicle_loss_hours, detour_data):
        vlh = pd.DataFrame(
            index=traffic_data.index,
            columns=[
                "vlh_traffic",
                "vlh_detour",
                "vlh_total",
                "euro_per_hour",
                "euro_vlh",
            ],
        )
        capacity = traffic_data["capacity"]
        diff_event_disr = self.duration - self.duration_disr

        if self.partofday == "daily":
            intensity = traffic_data["day_total"] / 24
            detour_time = detour_data["detour_time_day"]
        if self.partofday == "evening":
            intensity = traffic_data["evening_total"]
            detour_time = detour_data["detour_time_evening"]

        vlh = self.traffic_shockwave(vlh, capacity, intensity)
        vlh["vlh_traffic"] = vlh["vlh_traffic"].apply(
            lambda x: np.where(x < 0, 0, x)
        )  # all values below 0 -> 0
        vlh["vlh_traffic"] = vlh["vlh_traffic"].apply(
            lambda x: np.where(x > self.maximum, self.maximum, x)
        )
        # all values above maximum, limit to maximum
        vlh["vlh_detour"] = (
            intensity * ((1 - self.traffic_throughput) * self.duration) * detour_time
        ) / 60
        vlh["vlh_detour"] = vlh["vlh_detour"].apply(
            lambda x: np.where(x < 0, 0, x)
        )  # all values below 0 -> 0

        if (
            diff_event_disr > 0
        ):  # when the event is done, but the disruption continues after the event. Calculate extra detour times
            temp = (
                diff_event_disr * (detour_time * self.detour_traffic * detour_time) / 60
            )
            temp = temp.apply(
                lambda x: np.where(x < 0, 0, x)
            )  # all values below 0 -> 0
            vlh["vlh_detour"] = vlh["vlh_detour"] + temp

        vlh["vlh_total"] = vlh["vlh_traffic"] + vlh["vlh_detour"]

        if self.partofday == "daily":
            vlh["euro_per_hour"] = (
                (
                    traffic_data["day_freight"]
                    / traffic_data["day_total"]
                    * vehicle_loss_hours["freight"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["day_commute"]
                    / traffic_data["day_total"]
                    * vehicle_loss_hours["commute"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["day_business"]
                    / traffic_data["day_total"]
                    * vehicle_loss_hours["business"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["day_other"]
                    / traffic_data["day_total"]
                    * vehicle_loss_hours["other"]["vehicle_loss_hour"]
                )
            )
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type

        if self.partofday == "evening":
            vlh["euro_per_hour"] = (
                (
                    traffic_data["evening_freight"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["freight"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["evening_commute"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["commute"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["evening_business"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["business"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["evening_other"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["other"]["vehicle_loss_hour"]
                )
            )
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type
        vlh["euro_vlh"] = vlh["euro_per_hour"] * vlh["vlh_total"]
        return vlh

    def calculate_losses_from_table(self):
        """This function opens an existing table with traffic data and value of time to calculate losses based on detouring values. It also includes
        a traffic jam estimation.
        #TODO: check if gdf already exists from effectiveness measures.
        #TODO: If not: read feather file.
        #TODO: if yes: read gdf
        #TODO: koppelen van VVU aan de directe schade berekeningen
        """

        traffic_data = self.load_df(
            self.config["input"] / "losses", "traffic_intensities.csv"
        )
        dict1 = {
            "AS_VTG": "evening_total",
            "AS_FRGT": "evening_freight",
            "AS_COMM": "evening_commute",
            "AS_BUSS": "evening_business",
            "AS_OTHR": "evening_other",
            "ET_FRGT": "day_freight",
            "ET_COMM": "day_commute",
            "ET_BUSS": "day_business",
            "ET_OTHR": "day_other",
            "ET_VTG": "day_total",
            "afstand": "distance",
            "H_Cap": "capacity",
            "H_Stroken": "lanes",
        }
        traffic_data.rename(columns=dict1, inplace=True)

        detour_data = self.load_df(self.config["input"] / "losses", "detour_data.csv")
        dict2 = {
            "VA_AV_HWN": "detour_time_evening",
            "VA_RD_HWN": "detour_time_remaining",
            "VA_OS_HWN": "detour_time_morning",
            "VA_Etm_HWN": "detour_time_day",
        }
        detour_data.rename(columns=dict2, inplace=True)

        vehicle_loss_hours = self.vehicle_loss_hours(self.config["input"] / "losses")
        vlh = self.calc_vlh(traffic_data, vehicle_loss_hours, detour_data)
        return vlh


def save_gdf(gdf, save_path):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        edge_shp [str]: output path including extension for edges shapefile
        node_shp [str]: output path including extension for nodes shapefile
    Returns:
        None
    """
    # save to shapefile
    gdf.crs = "epsg:4326"  # TODO: decide if this should be variable with e.g. an output_crs configured

    for col in gdf.columns:
        if gdf[col].dtype == object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(save_path, driver="ESRI Shapefile", encoding="utf-8")
    logging.info("Results saved to: {}".format(save_path))


def find_route_ods(graph, od_nodes, weighing):
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
                edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing])[
                    0
                ]
                if "geometry" in graph[u][v][edge_key]:
                    pref_edges.append(graph[u][v][edge_key]["geometry"])
                else:
                    pref_edges.append(
                        LineString(
                            [graph.nodes[u]["geometry"], graph.nodes[v]["geometry"]]
                        )
                    )
                if "rfid" in graph[u][v][edge_key]:
                    match_list.append(graph[u][v][edge_key]["rfid"])

            # compile the road segments into one geometry
            pref_edges = MultiLineString(pref_edges)

            # save all data to lists (of lists)
            o_node_list.append(o[0])
            d_node_list.append(d[0])
            origin_list.append(o[1])
            destination_list.append(d[1])
            opt_path_list.append(pref_nodes)
            weighing_list.append(pref_route)
            match_ids_list.append(match_list)
            geometries_list.append(pref_edges)

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
    return pref_routes


def find_closest_node_attr(
    H, keyName, weighingName, originLabelContains, destLabelContains
):
    """Find the closest destination node with a certain attribute from all origin nodes

    Returns:
        originClosestDest [list of tuples]: list of the origin and destination node id and node name from the routes that are found
        list_no_path [list of tuples]: list of the origin and destination node id and node name from the origins/nodes that do not have a route between them
    """
    H.add_node("special", speciallabel="special")

    special_edges = []
    for n, ndat in H.nodes.data():
        if keyName in ndat:
            if destLabelContains in ndat[keyName]:
                special_edges.append((n, "special", {weighingName: 0}))

    H.add_edges_from(special_edges)

    list_no_path = []
    for n, ndat in H.nodes.data():
        if keyName in ndat:
            if originLabelContains in ndat[keyName]:
                if nx.has_path(H, n, "special"):
                    path = nx.shortest_path(
                        H, source=n, target="special", weight=weighingName
                    )
                    ndat["closest"] = path[
                        -2
                    ]  # Closest node with destLabelContains in keyName
                else:
                    list_no_path.append((n, ndat[keyName]))

    originClosestDest = [
        (
            (nn[0], nn[-1][keyName]),
            (nn[-1]["closest"], H.nodes[nn[-1]["closest"]][keyName]),
        )
        for nn in H.nodes.data()
        if "closest" in nn[-1]
    ]

    # Remove the special edges
    H.remove_edges_from([(n[0], n[1]) for n in H.edges.data() if n[1] == "special"])

    # Remove the closest attribute
    if originClosestDest:
        for ((o, o_name), (d, d_name)) in originClosestDest:
            del H.nodes[o]["closest"]

    return originClosestDest, list_no_path


def calc_pref_routes_closest_dest(
    graph,
    base_graph,
    weighing,
    crs,
    od_id,
    idName,
    origin_closest_dest,
    origins,
    nr_people_name,
    factor_out,
):
    # dataframe to save the preferred routes
    pref_routes = gpd.GeoDataFrame(
        columns=[
            "o_node",
            "d_node",
            "origin",
            "destination",
            "opt_path",
            weighing,
            "match_ids",
            "origin_cnt",
            "cnt_weight",
            "tot_miles",
            "geometry",
        ],
        geometry="geometry",
        crs="epsg:{}".format(crs),
    )

    # find the optimal route without (hazard) disruption
    for o, d in origin_closest_dest:
        # calculate the length of the preferred route
        pref_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=weighing)

        # save preferred route nodes
        pref_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=weighing)

        # found out which edges belong to the preferred path
        edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

        # Find the number of people per neighborhood
        nr_people_per_route_total = origins.loc[
            origins[od_id] == int(o[1].split("_")[-1]), nr_people_name
        ].iloc[0]
        nr_per_route = nr_people_per_route_total * factor_out

        pref_edges = []
        match_list = []
        length_list = []
        for u, v in edgesinpath:
            # get edge with the lowest weighing if there are multiple edges that connect u and v
            edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing])[0]
            if "geometry" in graph[u][v][edge_key]:
                pref_edges.append(graph[u][v][edge_key]["geometry"])
            else:
                pref_edges.append(
                    LineString([graph.nodes[u]["geometry"], graph.nodes[v]["geometry"]])
                )
            if idName in graph[u][v][edge_key]:
                match_list.append(graph[u][v][edge_key][idName])
            if "length" in graph[u][v][edge_key]:
                length_list.append(graph[u][v][edge_key]["length"])

            # Add the number of people that go from the origin to a destination to the road segments.
            # For now, each road segment in a route gets attributed all the people that are taking that route.
            base_graph[u][v][edge_key]["opt_cnt"] = (
                base_graph[u][v][edge_key]["opt_cnt"] + nr_per_route
            )

        # compile the road segments into one geometry
        pref_edges = MultiLineString(pref_edges)
        pref_routes = pref_routes.append(
            {
                "o_node": o[0],
                "d_node": d[0],
                "origin": o[1],
                "destination": d[1],
                "opt_path": pref_nodes,
                weighing: pref_route,
                "match_ids": match_list,
                "origin_cnt": nr_people_per_route_total,
                "cnt_weight": nr_per_route,
                "tot_miles": sum(length_list) / 1609,
                "geometry": pref_edges,
            },
            ignore_index=True,
        )

    return pref_routes, base_graph


def calc_routes_closest_dest(
    graph,
    base_graph,
    list_closest,
    pref_routes,
    weighing,
    origin,
    dest,
    od_id,
    hazname,
    threshold_destinations,
    factor_hospital,
    nr_people_name,
):
    pp_no_delay = [0]
    pp_delayed = [0]
    extra_weights = [0]
    extra_miles_total = [0]
    list_disrupted_destinations = []

    # find the optimal route with hazard disruption
    for o, d in list_closest:
        # Check if the destination that is accessed, is flooded
        try:
            if graph.nodes[d[0]][hazname] > threshold_destinations:
                list_disrupted_destinations.append((o, d))
                continue
        except KeyError as e:
            logging.warning(
                f"The destination nodes do not contain the required attribute '{hazname}',"
                f" please make sure that the hazard overlay is done correctly by rerunning the 'network.ini'"
                f" and checking the output files."
            )
            quit()

        # calculate the length of the preferred route
        alt_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=weighing)

        # save preferred route nodes
        alt_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=weighing)

        # Find the number of people per neighborhood
        nr_people_per_route_total = origin.loc[
            origin[od_id] == int(o[1].split("_")[-1]), nr_people_name
        ].iloc[0]
        nr_per_route = nr_people_per_route_total * factor_hospital

        # find out which edges belong to the preferred path
        edgesinpath = list(zip(alt_nodes[0:], alt_nodes[1:]))

        # calculate the total length of the alternative route (in miles)
        # Find the road segments that are used for the detour to the same or another hospital
        length_list = []
        for u, v in edgesinpath:
            # get edge with the lowest weighing if there are multiple edges that connect u and v
            edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing])[0]

            # Add the number of people that need to go to a destination to the road segments. For now, each road segment in a route
            # gets attributed all the people that are taking that route.
            base_graph[u][v][edge_key][hazname[:-3] + "_P"] = (
                base_graph[u][v][edge_key][hazname[:-3] + "_P"] + nr_per_route
            )

            if "length" in graph[u][v][edge_key]:
                length_list.append(graph[u][v][edge_key]["length"])

        alt_dist = sum(length_list)

        # If the destination is different from the origin, the destination is further than without hazard disruption
        if pref_routes.loc[
            (pref_routes["origin"] == o[1]) & (pref_routes["destination"] == d[1])
        ].empty:
            # subtract the length/time of the optimal route from the alternative route
            extra_dist = (
                alt_route
                - pref_routes.loc[pref_routes["origin"] == o[1], weighing].iloc[0]
            )
            extra_miles = (
                alt_dist
                - pref_routes.loc[pref_routes["origin"] == o[1], "tot_miles"].iloc[0]
            )
            pp_delayed.append(nr_per_route)
            extra_weights.append(extra_dist)
            extra_miles_total.append(extra_miles)
        else:
            pp_no_delay.append(nr_per_route)

        # compile the road segments into one geometry
        # alt_edges = MultiLineString(alt_edges)

        # Add the number of patients to the total number of patients that go to that hospital
        dest.loc[dest[od_id] == int(d[1].split("_")[-1]), hazname[:-3] + "_P"] = (
            dest.loc[dest[od_id] == int(d[1].split("_")[-1]), hazname[:-3] + "_P"].iloc[
                0
            ]
            + nr_per_route
        )

    return (
        base_graph,
        dest,
        list_disrupted_destinations,
        pp_no_delay,
        pp_delayed,
        extra_weights,
        extra_miles_total,
    )


def load_origins(config):
    od_path = config["static"] / "output_graph" / "origin_destination_table.feather"
    od = gpd.read_feather(od_path)
    origin = od.loc[od["o_id"].notna()]
    del origin["d_id"]
    del origin["match_ids"]
    return origin


def load_destinations(config):
    od_path = config["static"] / "output_graph" / "origin_destination_table.feather"
    od = gpd.read_feather(od_path)
    destination = od.loc[od["d_id"].notna()]
    del destination["o_id"]
    del destination["match_ids"]
    return destination


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
