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


# -*- coding: utf-8 -*-
import copy
import logging
from typing import Optional, Union

import geopandas as gpd
import networkx as nx
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from tqdm import tqdm

from ra2ce.io.readers.graph_pickle_reader import GraphPickleReader


class OriginClosestDestination:
    """The origin closest destination analyses using NetworkX graphs.

    Attributes:
        config: A dictionary with the configuration details on how to create and adjust the network.
        graphs: A dictionary with one or multiple NetworkX graphs.
    """

    def __init__(self, config: dict, analysis: dict, hazard_names: pd.DataFrame):
        self.crs = 4326  # TODO PUT IN DOCUMENTATION OR MAKE CHANGABLE
        self.unit = "km"
        if "threshold" in analysis:
            self.network_threshold = analysis["threshold"]
        self.threshold_destinations = 0  # TODO MAKE PARAMETER IN ANALYSES.INI
        self.weighing = analysis["weighing"]
        self.o_name = config["origins_destinations"]["origins_names"]
        self.d_name = config["origins_destinations"]["destinations_names"]
        self.od_id = config["origins_destinations"]["id_name_origin_destination"]
        self.origin_out_fraction = config["origins_destinations"]["origin_out_fraction"]
        self.origin_count = config["origins_destinations"]["origin_count"]
        self.od_key = "od_id"
        self.id_name = (
            config["network"]["file_id"]
            if config["network"]["file_id"] is not None
            else "rfid"
        )
        self.analysis = analysis
        self.config = config
        self.hazard_names = hazard_names

        self.destination_names = None
        self.destination_key = None
        if "category" in config["origins_destinations"]:
            self.destination_key = "category"
            self.destination_key_value = config["origins_destinations"]["category"]

        self.results_dict = {}

    @staticmethod
    def read(graph_file):
        _pickle_reader = GraphPickleReader()
        g = _pickle_reader.read(graph_file)
        return g

    def optimal_route_origin_closest_destination(self):
        """Calculates per origin the location of its closest destination"""
        graph = self.read(self.config["files"]["origins_destinations_graph"])

        # Load the origins and destinations
        origins = self.load_origins()
        destinations = self.load_destinations()

        # Create a copy of the graph to save all the results in
        base_graph = copy.deepcopy(graph)

        # Add a column for the number of people that go to a certain destination, per flood map
        col_name = "noHaz"

        if self.destination_key:
            self.destination_names = list(
                destinations[self.config["origins_destinations"]["category"]].unique()
            )
            self.destination_names_short = {
                dn: f"D{i+1}" for i, dn in enumerate(self.destination_names)
            }
            logging.info(self.destination_names_short)  # TODO: WRITE SOMEWHERE

            for i, dn in self.destination_names_short.items():
                destinations[col_name + "_P" + dn] = 0

            (
                base_graph,
                origins,
                destinations,
                list_disrupted_dest,
                optimal_routes_gdf,
            ) = self.find_multiple_closest_locations(
                graph, base_graph, origins, destinations, col_name
            )
        else:
            destinations[col_name + "_P"] = 0
            (
                base_graph,
                origins,
                destinations,
                list_disrupted_dest,
                optimal_routes_gdf,
            ) = self.find_closest_location(
                graph, base_graph, origins, destinations, col_name
            )

        cnt_per_destination = (
            optimal_routes_gdf.groupby("destination")["origin_cnt"].sum().reset_index()
        )
        for dest, origin_cnt in zip(
            cnt_per_destination["destination"],
            cnt_per_destination["origin_cnt"],
        ):
            destinations.loc[
                destinations[self.od_id] == int(dest.split("_")[-1]), "origin_cnt"
            ] = origin_cnt

        return base_graph, optimal_routes_gdf, destinations

    def multi_link_origin_closest_destination(self):
        """Calculates per origin the location of its closest destination with hazard disruption"""
        graph = self.read(self.config["files"]["origins_destinations_graph_hazard"])

        # Load the origins and destinations
        origins = self.load_origins()
        destinations = self.load_destinations()

        # Create a copy of the graph to save all the results in
        base_graph = copy.deepcopy(graph)

        if self.destination_key:
            self.destination_names = list(
                destinations[self.config["origins_destinations"]["category"]].unique()
            )
            self.destination_names_short = {
                dn: f"D{i+1}" for i, dn in enumerate(self.destination_names)
            }
            logging.info(self.destination_names_short)  # TODO: WRITE SOMEWHERE

        aggregated = []
        opt_routes_aggregated = []

        # Calculate the criticality
        hazards = [
            self.hazard_names.loc[
                self.hazard_names["File name"] == hazard, "RA2CE name"
            ].values[0]
            for hazard in self.config["hazard_names"]
        ]
        hazards.sort()
        for hazard_name in hazards:
            self.results_dict = dict()
            self.results_dict["Hazard"] = [hazard_name]

            # Add a column for the number of people that go to a certain destination, per flood map
            if self.destination_key:
                for i, dn in self.destination_names_short.items():
                    destinations[hazard_name + "_P" + dn] = 0
            else:
                destinations[hazard_name + "_P"] = 0

            # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
            h = copy.deepcopy(graph)

            edges_remove = [
                e for e in graph.edges.data(keys=True) if hazard_name in e[-1]
            ]
            edges_remove = [e for e in edges_remove if (e[-1][hazard_name] is not None)]
            edges_remove = [
                e
                for e in edges_remove
                if (e[-1][hazard_name] > float(self.network_threshold))
                & ("bridge" not in e[-1])
            ]
            h.remove_edges_from(edges_remove)

            if self.destination_key:
                (
                    base_graph,
                    origins,
                    destinations,
                    list_disrupted_dest,
                    optimal_routes_gdf,
                ) = self.find_multiple_closest_locations(
                    h,
                    base_graph,
                    origins,
                    destinations,
                    hazard_name,
                    hazard_name,
                )
            else:
                (
                    base_graph,
                    origins,
                    destinations,
                    list_disrupted_dest,
                    optimal_routes_gdf,
                ) = self.find_closest_location(
                    h,
                    base_graph,
                    origins,
                    destinations,
                    hazard_name,
                    hazard_name,
                )

            ## THE BELOW IS NOT USED AT THE MOMENT - COULD BE IMPLEMENTED AS OPTION AT A LATER STAGE ##
            # # Now calculate for the routes that were going to a flooded destination, another non-flooded destination
            # # There can be nodes that are both origins and destinations. The flooded destinations are removed from
            # # the graph.
            # list_dests_flooded_destination_only = [dest[-1][0] for dest in list_disrupted_dest if
            #                                        not self.o_name in dest[-1][-1]]
            # list_dests_flooded_destination_and_origin = [dest[-1][0] for dest in list_disrupted_dest if
            #     self.o_name in dest[-1][-1] and self.d_name in dest[-1][-1]]
            # list_origins_without_routes = [dest[0][0] for dest in list_disrupted_dest]
            # list_origins_with_routes = [n for n in h.nodes() if n not in list_origins_without_routes]
            #
            # disr_by_flood = len(list_dests_flooded_destination_only + list_dests_flooded_destination_and_origin)
            #
            # if disr_by_flood > 0:
            #     # Remove the flooded destination nodes
            #     h.remove_nodes_from(list_dests_flooded_destination_only)
            #
            #     for node in list_dests_flooded_destination_and_origin:
            #         # Delete the destination name from the "od_id" attribute of the nodes of which the destination is
            #         # flooded.
            #         od_id = h.nodes[node]["od_id"]
            #         h.nodes[node]["od_id"] = ",".join([od for od in od_id.split(",") if self.d_name not in od])
            #
            #     # Remove the origin nodes that already have a destination
            #     h.remove_nodes_from(list_origins_with_routes)
            #
            #     # Search for the next closest location
            #     base_graph, origins, destinations, list_disrupted_dest, results_dict_update = self.find_closest_location(h,
            #                                                                                                        base_graph,
            #                                                                                                        origins,
            #                                                                                                        destinations,
            #                                                                                                        hazard_name,
            #                                                                                                        self.d_name)
            #
            #     self.results_dict['Nr. no access'] = [
            #         self.results_dict['Nr. no access'][0] + self.results_dict_update['Nr. no access'][0]]
            #
            # self.results_dict.update({
            #     "Flooded destination": [disr_by_flood]
            # })
            ## THE ABOVE IS NOT USED AT THE MOMENT - COULD BE IMPLEMENTED AS OPTION AT A LATER STAGE ##

            aggregated.append(pd.DataFrame(self.results_dict))

            optimal_routes_gdf["name"] = hazard_name
            opt_routes_aggregated.append(optimal_routes_gdf)

        # Create one dataframe from the aggregated results
        aggregated = pd.concat(aggregated)
        opt_routes_aggregated = pd.concat(opt_routes_aggregated)

        return base_graph, origins, destinations, aggregated, opt_routes_aggregated

    def get_route_length(self, graph, origin_node, destination_node):
        # calculate the length of the preferred route
        return nx.dijkstra_path_length(
            graph, origin_node, destination_node, weight=self.weighing
        )

    def compare_route_with_without_disruption(
        self, pref_routes, nr_per_route, o_name, d_name, alt_route, alt_dist
    ):
        pp_no_delay = [0]
        pp_delayed = [0]
        extra_weights = [0]
        extra_kms_total = [0]

        # If the destination is different from the origin, the destination is further than without hazard disruption
        if pref_routes.loc[
            (pref_routes["origin"] == o_name) & (pref_routes["destination"] == d_name)
        ].empty:
            # subtract the length/time of the optimal route from the alternative route
            extra_dist = (
                alt_route
                - pref_routes.loc[pref_routes["origin"] == o_name, self.weighing].iloc[
                    0
                ]
            )
            extra_km = (
                alt_dist
                - pref_routes.loc[pref_routes["origin"] == o_name, "tot_km"].iloc[0]
            )
            pp_delayed.append(nr_per_route)
            extra_weights.append(extra_dist)
            extra_kms_total.append(extra_km)
        else:
            pp_no_delay.append(nr_per_route)

        if pp_no_delay != [0]:
            self.results_dict["Nr. no delay"] = [round(sum(pp_no_delay))]
        if pp_delayed != [0]:
            self.results_dict["Nr. delayed"] = [round(sum(pp_delayed))]
        if extra_weights != [0]:
            self.results_dict[f"Total extra detour {self.weighing}"] = [
                sum(extra_weights)
            ]
        if extra_kms_total != [0]:
            self.results_dict[f"Total extra detour distance ({self.unit})"] = [
                sum(extra_kms_total)
            ]

    def get_route_path(
        self, graph, base_graph, origin_node, destination_node, nr_from_origin, col_name
    ):
        # Get the nodes of the optimal route
        route_nodes = nx.dijkstra_path(
            graph, origin_node, destination_node, weight=self.weighing
        )

        # find out which edges belong to the preferred path
        edgesinpath = list(zip(route_nodes[0:], route_nodes[1:]))

        # calculate the total length of the alternative route
        # Find the road segments that are used for the detour to the same or another destination
        pref_edges = []
        length_list = []
        for u, v in edgesinpath:
            # get edge with the lowest weighing if there are multiple edges that connect u and v
            _uv_graph = graph[u][v]
            edge_key = sorted(
                _uv_graph, key=lambda x, _fgraph=_uv_graph: _fgraph[x][self.weighing]
            )[0]
            _uv_graph_edge = _uv_graph[edge_key]
            if "geometry" in _uv_graph_edge:
                pref_edges.append(_uv_graph_edge["geometry"])
            else:
                pref_edges.append(
                    LineString([graph.nodes[u]["geometry"], graph.nodes[v]["geometry"]])
                )

            if "length" in _uv_graph_edge:
                length_list.append(_uv_graph_edge["length"])

            # Add the number of people that need to go to a destination to the road segments. For now, each road segment in a route
            # gets attributed all the people that are taking that route.
            base_graph[u][v][edge_key][col_name] = (
                base_graph[u][v][edge_key][col_name] + nr_from_origin
            )

        pref_edges = MultiLineString(pref_edges)

        return base_graph, sum(length_list), pref_edges

    def get_nr_people_on_route(self, origins, origin_node):
        # Find the number of people per neighborhood
        try:
            nr_people_per_route_total = origins.loc[
                origins[self.od_id] == int(origin_node.split("_")[-1]),
                self.origin_count,
            ].iloc[0]
        except IndexError:
            origin_node = [a for a in origin_node.split(",") if self.o_name in a][0]
            nr_people_per_route_total = origins.loc[
                origins[self.od_id] == int(origin_node.split("_")[-1]),
                self.origin_count,
            ].iloc[0]
        nr_per_route = nr_people_per_route_total * self.origin_out_fraction
        return nr_per_route

    def update_destinations(
        self, destinations, destination_name, nr_per_route, col_name
    ):
        dest_ids = [
            int(d.split("_")[-1])
            for d in [dest for dest in destination_name.split(",")]
            if self.d_name in d
        ]

        # Add the number of people to the total number of people that go to that destination
        destinations.loc[destinations[self.od_id].isin(dest_ids), col_name] = (
            destinations.loc[destinations[self.od_id].isin(dest_ids), col_name].sum()
            + nr_per_route
        )
        return destinations

    def update_origins(self, origins, other, col_name):
        # Attribute to the origins that don't have access that they do not have any access
        if len(other) > 0:
            for oth in other:
                origins.loc[
                    origins[self.od_id] == int(oth[-1].split("_")[-1]),
                    col_name,
                ] = "no access"
        return origins

    def get_nr_without_access(
        self,
        origins: gpd.GeoDataFrame,
        origins_without_access: list,
        add_key_name: str = None,
    ):
        # Calculate the number of people that cannot access any destination
        origins_no_access = [
            o
            for o in [
                oth[-1].split(",") if len(origins_without_access) > 0 else 0
                for oth in origins_without_access
            ]
        ]
        origins_no_access = [
            int(item.split("_")[-1])
            for sublist in origins_no_access
            for item in sublist
        ]

        pp_no_access = [
            round(
                (
                    origins.loc[
                        origins[self.od_id].isin(origins_no_access), self.origin_count
                    ]
                    * self.origin_out_fraction
                ).sum()
            )
            if len(origins_no_access) > 0
            else 0
        ]

        self.results_dict[f"Nr. no access{add_key_name}"] = pp_no_access

    def find_closest_location(
        self,
        disrupted_graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        base_graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        origins: gpd.GeoDataFrame,
        destinations: gpd.GeoDataFrame,
        column_name: str,
        hazard_name: str = None,
        pref_routes: gpd.GeoDataFrame = None,
    ):
        """Find the closest destination nodes with a certain attribute from all origin nodes for a single destination
        Args:
            disrupted_graph: NetworkX graph with origin and destination nodes and disrupted edges removed
            base_graph: Original NetworkX graph
            origins: GeoDataFrame containing the origins
            destinations: GeoDataFrame containing the destinations
            column_name: the name of the column which will be added to the base_graph, origins, destinations, and self.results_dict
            hazard_name: the name of the hazard (which is an attribute of the edges in the disrupted_graph)
            pref_routes: GeoDataFrame containing the preferred routes without disruption

        Returns:
            base_graph:
            origins: the updated origins GeoDataFrame
            destinations: the updated destinations GeoDataFrame
            list_disrupted_destinations [list of tuples]: list of the origin and destination node id and node name from the origins/nodes that do not have a route between them
        """
        name_save = column_name + "_{}"
        nx.set_edge_attributes(base_graph, 0, name_save.format("P"))

        # Add a column to the neighborhoods, to indicate if they have access to any destination POI.
        # The origins without access are indicated later
        origins[name_save.format("A")] = "access"

        disrupted_graph.add_node("special", speciallabel="special")

        special_edges = []
        for n, ndat in disrupted_graph.nodes.data():
            if self.od_key in ndat and self.d_name in ndat[self.od_key]:
                special_edges.append((n, "special", {self.weighing: 0}))

        disrupted_graph.add_edges_from(special_edges)

        optimal_routes = []
        list_disrupted_destinations = []
        list_no_path = []
        for n_ndat in tqdm(disrupted_graph.nodes.data(), desc="Finding optimal routes"):
            _new_origins = self._find_optimal_routes(
                list_no_path,
                n_ndat,
                disrupted_graph,
                hazard_name,
                list_disrupted_destinations,
                pref_routes,
                "special",
                name_save,
                optimal_routes,
                origins,
                base_graph,
                destinations,
            )

            if _new_origins is not None:
                origins = _new_origins
                self.get_nr_without_access(origins, list_no_path)

        # Remove the special edges
        disrupted_graph.remove_edges_from(
            [(n[0], n[1]) for n in disrupted_graph.edges.data() if n[1] == "special"]
        )

        # Remove the closest attribute from the nodes
        origin_closest_dst = [
            nn[0] for nn in disrupted_graph.nodes.data() if "closest" in nn[-1]
        ]

        if origin_closest_dst:
            for o in origin_closest_dst:
                del disrupted_graph.nodes[o]["closest"]

            optimal_routes_gdf = pd.concat(optimal_routes)

        return (
            base_graph,
            origins,
            destinations,
            list_disrupted_destinations,
            optimal_routes_gdf,
        )

    def _find_optimal_routes(
        self,
        list_no_path: list,
        n_ndat: tuple,
        disrupted_graph,
        hazard_name: str,
        list_disrupted_destinations: list,
        pref_routes: gpd.GeoDataFrame,
        dest_name: str,
        name_save: str,
        optimal_routes: list,
        origins,
        base_graph,
        destinations,
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Refactored method to avoid duplication of code between `find_closest_location` and `find_multiple_closest_locations` with subtile differences:
        - The first would not use a `dest_name` attribute.
        - The second one would use 'ndat["closest"]' instead of the assigned 'closest_dest'

        Returns:
            Optional[gpd.GeoDataFrame]: When the wrapper for-loop needs to go into the next iteration it will return 'None'. Otherwise a resulting `gpd.GeoDataFrame`.
        """
        n, ndat = n_ndat
        if self.od_key in ndat and self.o_name in ndat[self.od_key]:
            if nx.has_path(disrupted_graph, n, dest_name):
                path = nx.shortest_path(
                    disrupted_graph,
                    source=n,
                    target=dest_name,
                    weight=self.weighing,
                )
                # Closest node with destLabelContains in keyName
                ndat["closest"] = path[-2]
                closest_dest = ndat["closest"]

                # Check if the destination that is accessed, is flooded
                if hazard_name:
                    try:
                        if (
                            disrupted_graph.nodes[closest_dest][hazard_name]
                            > self.threshold_destinations
                        ):
                            list_disrupted_destinations.append(
                                (
                                    (n, ndat[self.od_key]),
                                    (
                                        closest_dest,
                                        disrupted_graph.nodes[closest_dest][
                                            self.od_key
                                        ],
                                    ),
                                )
                            )
                            return None
                    except KeyError as e:
                        logging.error(
                            f"The destination nodes do not contain the required attribute '{hazard_name}',"
                            f" please make sure that the hazard overlay is done correctly by rerunning the 'network.ini'"
                            f" and checking the output files."
                        )
                        raise e

                nr_per_route = self.get_nr_people_on_route(origins, ndat[self.od_key])
                base_graph, route_path, route_geoms = self.get_route_path(
                    disrupted_graph,
                    base_graph,
                    n,
                    closest_dest,
                    nr_per_route,
                    name_save.format("P"),
                )
                if pref_routes:
                    route_length = self.get_route_length(
                        disrupted_graph, n, closest_dest
                    )
                    self.compare_route_with_without_distruption(
                        pref_routes,
                        nr_per_route,
                        ndat[self.od_key],
                        disrupted_graph.nodes[closest_dest],
                        route_length,
                        route_path,
                    )
                destinations = self.update_destinations(
                    destinations,
                    disrupted_graph.nodes[closest_dest][self.od_key],
                    nr_per_route,
                    name_save.format("P"),
                )

                if route_geoms:
                    optimal_routes.append(
                        gpd.GeoDataFrame(
                            {
                                "o_node": n,
                                "d_node": closest_dest,
                                "origin": ndat[self.od_key],
                                "destination": disrupted_graph.nodes[closest_dest][
                                    self.od_key
                                ],
                                self.weighing: route_path,
                                "origin_cnt": nr_per_route,
                                "geometry": [route_geoms],
                                "category": dest_name,
                            },
                            crs=self.crs,
                        )
                    )
            else:
                list_no_path.append((n, ndat[self.od_key]))

        return self.update_origins(origins, list_no_path, name_save.format("A"))

    def find_multiple_closest_locations(
        self,
        disrupted_graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        base_graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        origins: gpd.GeoDataFrame,
        destinations: gpd.GeoDataFrame,
        column_name: str,
        hazard_name: str = None,
        pref_routes: gpd.GeoDataFrame = None,
    ):
        """Find the closest destination nodes with a certain attribute from all origin nodes for multiple destinations
        Args:
            disrupted_graph: NetworkX graph with origin and destination nodes and disrupted edges removed
            base_graph: Original NetworkX graph
            origins: GeoDataFrame containing the origins
            destinations: GeoDataFrame containing the destinations
            column_name: the name of the column which will be added to the base_graph, origins, destinations, and self.results_dict
            hazard_name: the name of the hazard
            pref_routes: GeoDataFrame containing the preferred routes without disruption

        Returns:
            base_graph:
            origins: the updated origins GeoDataFrame
            destinations: the updated destinations GeoDataFrame
            list_disrupted_destinations [list of tuples]: list of the origin and destination node id and node name from the origins/nodes that do not have a route between them
        """

        optimal_routes = []
        for dest_name in self.destination_names:
            name_save = column_name + "_{}" + self.destination_names_short[dest_name]
            nx.set_edge_attributes(base_graph, 0, name_save.format("P"))

            # Add a column to the neighborhoods, to indicate if they have access to any destination POI.
            # The origins without access are indicated later
            origins[name_save.format("A")] = "access"

            disrupted_graph.add_node(dest_name, speciallabel=dest_name)

            special_edges = []
            for n, ndat in disrupted_graph.nodes.data():
                if (
                    self.od_key in ndat
                    and self.destination_key in ndat
                    and ndat[self.destination_key] == dest_name
                ):
                    special_edges.append(
                        (n, ndat[self.destination_key], {self.weighing: 0})
                    )

            disrupted_graph.add_edges_from(special_edges)

            list_disrupted_destinations = []
            list_no_path = []
            for n_ndat in tqdm(
                disrupted_graph.nodes.data(),
                desc=f"Finding optimal routes to {dest_name}",
            ):
                _new_origins = self._find_optimal_routes(
                    list_no_path,
                    n_ndat,
                    disrupted_graph,
                    hazard_name,
                    list_disrupted_destinations,
                    pref_routes,
                    dest_name,
                    name_save,
                    optimal_routes,
                    origins,
                    base_graph,
                    destinations,
                )

                if _new_origins is not None:
                    origins = _new_origins
                    self.get_nr_without_access(origins, list_no_path, f" {dest_name}")

            # Remove the special edges
            disrupted_graph.remove_edges_from(
                [
                    (n[0], n[1])
                    for n in disrupted_graph.edges.data()
                    if n[1] == dest_name
                ]
            )

            # Remove the closest attribute from the nodes
            for o in [
                nn[0] for nn in disrupted_graph.nodes.data() if "closest" in nn[-1]
            ]:
                del disrupted_graph.nodes[o]["closest"]

        optimal_routes_gdf = pd.concat(optimal_routes)

        return (
            base_graph,
            origins,
            destinations,
            list_disrupted_destinations,
            optimal_routes_gdf,
        )

    def calc_pref_routes_closest_dest(
        self,
        graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        base_graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        origin_closest_dest,
        origins,
    ):
        # dataframe to save the optimal routes
        pref_routes = gpd.GeoDataFrame(
            columns=[
                "o_node",
                "d_node",
                "origin",
                "destination",
                "opt_path",
                self.weighing,
                "match_ids",
                "origin_cnt",
                "cnt_weight",
                "tot_km",
                "geometry",
            ],
            geometry="geometry",
            crs="epsg:{}".format(self.crs),
        )

        # find the optimal route without (hazard) disruption
        for o, d in tqdm(origin_closest_dest, desc="Finding optimal routes"):
            # calculate the length of the preferred route
            pref_route = nx.dijkstra_path_length(
                graph, o[0], d[0], weight=self.weighing
            )

            # save preferred route nodes
            pref_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=self.weighing)

            # found out which edges belong to the preferred path
            edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

            # Find the number of people per neighborhood
            try:
                nr_people_per_route_total = origins.loc[
                    origins[self.od_id] == int(o[1].split("_")[-1]), self.origin_count
                ].iloc[0]
            except IndexError:
                origin_node = [a for a in o[1].split(",") if self.o_name in a][0]
                nr_people_per_route_total = origins.loc[
                    origins[self.od_id] == int(origin_node.split("_")[-1]),
                    self.origin_count,
                ].iloc[0]
            nr_per_route = nr_people_per_route_total * self.origin_out_fraction

            pref_edges = []
            match_list = []
            length_list = []
            for u, v in edgesinpath:
                # get edge with the lowest weighing if there are multiple edges that connect u and v
                _uv_graph = graph[u][v]
                edge_key = sorted(
                    _uv_graph,
                    key=lambda x, _fgraph=_uv_graph: _fgraph[x][self.weighing],
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
                if self.id_name in _uv_graph_edge:
                    match_list.append(_uv_graph_edge[self.id_name])
                if "length" in _uv_graph_edge:
                    length_list.append(_uv_graph_edge["length"])

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
                    self.weighing: pref_route,
                    "match_ids": match_list,
                    "origin_cnt": nr_people_per_route_total,
                    "cnt_weight": nr_per_route,
                    "tot_km": sum(length_list) / 1000,
                    "geometry": pref_edges,
                },
                ignore_index=True,
            )

        return pref_routes, base_graph

    def calc_routes_closest_dest(
        self,
        graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        base_graph: Union[nx.classes.Graph, nx.classes.MultiGraph],
        list_closest: list,
        origin: gpd.GeoDataFrame,
        dest: gpd.GeoDataFrame,
        hazname: str,
        pref_routes: gpd.GeoDataFrame = None,
    ):
        pp_no_delay = [0]
        pp_delayed = [0]
        extra_weights = [0]
        extra_kms_total = [0]
        list_disrupted_destinations = []

        # find the optimal route with hazard disruption
        for o, d in tqdm(
            list_closest,
            desc=f"Finding optimal routes with hazard disruption '{hazname}'.",
        ):
            # Check if the destination that is accessed, is flooded
            try:
                if graph.nodes[d[0]][hazname] > self.threshold_destinations:
                    list_disrupted_destinations.append((o, d))
                    continue
            except KeyError as e:
                logging.warning(
                    f"The destination nodes do not contain the required attribute '{hazname}',"
                    " please make sure that the hazard overlay is done correctly by rerunning the 'network.ini'"
                    " and checking the output files."
                    f"Further error details {e}"
                )
                quit()

            # calculate the length of the preferred route
            alt_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=self.weighing)

            # save preferred route nodes
            alt_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=self.weighing)

            # Find the number of people per neighborhood
            try:
                nr_people_per_route_total = origin.loc[
                    origin[self.od_id] == int(o[1].split("_")[-1]), self.origin_count
                ].iloc[0]
            except IndexError:
                origin_node = [a for a in o[1].split(",") if self.o_name in a][0]
                nr_people_per_route_total = origin.loc[
                    origin[self.od_id] == int(origin_node.split("_")[-1]),
                    self.origin_count,
                ].iloc[0]
            nr_per_route = nr_people_per_route_total * self.origin_out_fraction

            # find out which edges belong to the preferred path
            edgesinpath = list(zip(alt_nodes[0:], alt_nodes[1:]))

            # calculate the total length of the alternative route (in miles)
            # Find the road segments that are used for the detour to the same or another hospital
            length_list = []
            for u, v in edgesinpath:
                # get edge with the lowest weighing if there are multiple edges that connect u and v
                _uv_graph = graph[u][v]
                edge_key = sorted(
                    _uv_graph,
                    key=lambda x, _fgraph=_uv_graph: _fgraph[x][self.weighing],
                )[0]
                _uv_graph_edge = _uv_graph[edge_key]

                # Add the number of people that need to go to a destination to the road segments. For now, each road segment in a route
                # gets attributed all the people that are taking that route.
                base_graph[u][v][edge_key][hazname + "_P"] = (
                    base_graph[u][v][edge_key][hazname + "_P"] + nr_per_route
                )

                if "length" in _uv_graph_edge:
                    length_list.append(_uv_graph_edge["length"])

            alt_dist = sum(length_list)

            if pref_routes:
                # If the destination is different from the origin, the destination is further than without hazard disruption
                if pref_routes.loc[
                    (pref_routes["origin"] == o[1])
                    & (pref_routes["destination"] == d[1])
                ].empty:
                    # subtract the length/time of the optimal route from the alternative route
                    extra_dist = (
                        alt_route
                        - pref_routes.loc[
                            pref_routes["origin"] == o[1], self.weighing
                        ].iloc[0]
                    )
                    extra_km = (
                        alt_dist
                        - pref_routes.loc[pref_routes["origin"] == o[1], "tot_km"].iloc[
                            0
                        ]
                    )
                    pp_delayed.append(nr_per_route)
                    extra_weights.append(extra_dist)
                    extra_kms_total.append(extra_km)
                else:
                    pp_no_delay.append(nr_per_route)

            # compile the road segments into one geometry
            # alt_edges = MultiLineString(alt_edges)

            # Add the number of people to the total number of people that go to that destination
            dest.loc[dest[self.od_id] == int(d[1].split("_")[-1]), hazname + "_P"] = (
                dest.loc[
                    dest[self.od_id] == int(d[1].split("_")[-1]), hazname + "_P"
                ].iloc[0]
                + nr_per_route
            )

        return (
            base_graph,
            dest,
            list_disrupted_destinations,
            pp_no_delay,
            pp_delayed,
            extra_weights,
            extra_kms_total,
        )

    def load_origins(self):
        od_path = (
            self.config["static"] / "output_graph" / "origin_destination_table.feather"
        )
        od = gpd.read_feather(od_path)
        origin = od.loc[od["o_id"].notna()]
        del origin["d_id"]
        return origin

    def load_destinations(self):
        od_path = (
            self.config["static"] / "output_graph" / "origin_destination_table.feather"
        )
        od = gpd.read_feather(od_path)
        destination = od.loc[od["d_id"].notna()]
        del destination["o_id"]
        return destination

    def difference_length_with_without_hazard(self, with_hazard, without_hazard):
        with_hazard.rename(columns={"length": "lengthDisr"}, inplace=True)
        without_hazard.rename(columns={"length": "lengthNorm"}, inplace=True)
        diff_length_bc_hazard = pd.merge(
            with_hazard,
            without_hazard[["lengthNorm", "origin", "destination"]],
            on=["origin", "destination"],
            how="left",
        )
        diff_length_bc_hazard["difference"] = (
            diff_length_bc_hazard["lengthDisr"].values
            - diff_length_bc_hazard["lengthNorm"].values
        )
        return diff_length_bc_hazard
