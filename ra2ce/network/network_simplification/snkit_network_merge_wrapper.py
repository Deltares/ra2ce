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

import logging
from collections import defaultdict

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from networkx import MultiGraph
from shapely.geometry import LineString, MultiLineString, MultiPoint, Point
from shapely.ops import linemerge
from snkit.network import Network as SnkitNetwork
from tqdm import tqdm

NxGraph = nx.Graph | nx.MultiGraph | nx.MultiDiGraph


"""
Disclaimer!

This file contains several complex logic introduced in feature #277.
At the moment it was not possible to streamline / improve it further than
its current state.
"""


def merge_edges(
    snkit_network: SnkitNetwork,
    networkx_graph: NxGraph,
    aggregate_func: str | dict,
    by: str | list,
    id_col: str,
) -> SnkitNetwork:
    """
    Merges the edges of a given `snkit.network.Network`.

    Args:
        snkit_network (SnkitNetwork): network to merge.
        networkx_graph (NxGraph): networkx graph to merge
        aggregate_func (str | dict): Aggregation function to apply.
        by (str | list): Arguments (column names).
        id_col (str, optional): Name of the column representing the 'id'.

    Returns:
        SnkitNetwork: _description_
    """

    def node_connectivity_degree(node, snkit_network: SnkitNetwork) -> int:
        return len(
            snkit_network.edges[
                (snkit_network.edges.from_id == node)
                | (snkit_network.edges.to_id == node)
            ]
        )

    def get_edge_ids_to_update(edges_list: list) -> list:
        ids_to_update = []
        for edges in edges_list:
            ids_to_update.extend(edges.id.tolist())
        return ids_to_update

    def get_merged_edges(
        paths_to_group: list,
        by: list,
        aggfunc: str | dict,
        net: SnkitNetwork,
    ) -> gpd.GeoDataFrame:
        updated_edges = gpd.GeoDataFrame(
            columns=net.edges.columns, crs=net.edges.crs
        )  # merged edges

        for edge_path in tqdm(paths_to_group, desc="merge_edge_paths"):
            # Convert None values to a placeholder value
            placeholder = "None"
            for col in by:
                edge_path[col] = edge_path[col].fillna(placeholder)
            merged_edges = _get_merge_edge_paths(edge_path, by, aggfunc, net)
            updated_edges = pd.concat([updated_edges, merged_edges], ignore_index=True)

        updated_edges_gdf = gpd.GeoDataFrame(updated_edges, geometry="geometry")
        updated_edges_gdf.set_crs(net.edges.crs, inplace=True)
        updated_edges_gdf = updated_edges_gdf.drop(columns=["id"])
        return updated_edges_gdf

    def filter_node(_node_set: set, _degrees: int) -> set:
        _filtered = set()
        for _node_id in _node_set:
            # Get the predecessors (antecedents) and successors (precedents) to make sure for to filter correctly
            # For _node_set with all degree 2: this filters on the nodes that have only one predecessor and successor.
            # E.g. filters on 2 in 1->2, 1->5, 2->3, 3->4, 3->5
            # For _node_set with all degree 4: Check if the predecessors and successors are the same nodes.
            # E.g. filters on 2 in 1->2, 2->3, 2->1, 3->2.
            predecessors = list(networkx_graph.predecessors(_node_id))
            successors = list(networkx_graph.successors(_node_id))

            # Check the degree of the _node_set and the corresponding criterium.
            if (_degrees == 2 and len(predecessors) == len(successors) == 1) or (
                _degrees == 4 and sorted(predecessors) == sorted(successors)
            ):
                _filtered.add(_node_id)
        return _filtered

    def get_edge_paths(node_set: set, _snkit_network: SnkitNetwork) -> list:
        def get_adjacency_list(
            edges_gdf: gpd.GeoDataFrame, from_id_column: str, to_id_column: str
        ) -> defaultdict:
            # Convert the edges of a GeoDataFrame to an adjacency list using vectorized operations.
            _edge_dict = defaultdict(set)
            # Extract the 'from_id' and 'to_id' columns as numpy arrays for efficient processing
            from_ids = edges_gdf[from_id_column].values
            to_ids = edges_gdf[to_id_column].values
            # Vectorized operation to populate the adjacency list
            for from_id, to_id in np.nditer([from_ids, to_ids]):
                _edge_dict[int(from_id)].add(int(to_id))
                _edge_dict[int(to_id)].add(int(from_id))

            return _edge_dict

        def retrieve_edge(node1: int | float, node2: int | float) -> gpd.GeoDataFrame:
            """Retrieve the edge from snkit_network.edges GeoDataFrame between two nodes."""
            edge = _snkit_network.edges[
                (_snkit_network.edges["from_id"] == node1)
                & (_snkit_network.edges["to_id"] == node2)
            ]
            return edge if not edge.empty else None

        def construct_path(
            start_node: int | float, end_node: int | float, intermediate_nodes: list
        ) -> pd.DataFrame | None:
            path = []
            current_node = start_node
            _intermediates = intermediate_nodes.copy()

            _explored_nodes = []
            # Ensure we go through all the items.
            for _ in range(len(intermediate_nodes)):
                # Filter out nodes already used for edge retrieval
                _to_explore = filter(
                    lambda x: x not in _explored_nodes, intermediate_nodes
                )
                for _next_node in _to_explore:
                    _edge = retrieve_edge(current_node, _next_node)
                    if _edge is not None:
                        path.append(_edge)
                        _explored_nodes.append(_next_node)
                        current_node = _next_node

            final_edge = retrieve_edge(current_node, end_node)
            if final_edge is not None:
                path.append(final_edge)

            if len(path) > 0 and all(edge is not None for edge in path):
                return pd.concat(path)  # Combine edges into a single GeoDataFrame
            return None

        def find_and_append_degree_4_paths(_edge_paths: list) -> list:
            _edge_paths_results = _edge_paths
            boundary_nodes = list(node_path - filtered_degree_4_set)
            if len(boundary_nodes) == 2:
                from_node, to_node = boundary_nodes
                _intermediates = list(node_path & filtered_degree_4_set)

                # Construct and append the forward path
                forward_gdf = construct_path(from_node, to_node, _intermediates)
                if forward_gdf is not None:
                    _edge_paths_results.append(forward_gdf)

                # Construct and append the backward path
                backward_gdf = construct_path(to_node, from_node, _intermediates)
                if backward_gdf is not None:
                    _edge_paths_results.append(backward_gdf)
            return _edge_paths_results

        # Convert edges to an adjacency list using vectorized operations
        edge_dict = get_adjacency_list(
            edges_gdf=snkit_network.edges,
            from_id_column="from_id",
            to_id_column="to_id",
        )
        _edge_paths: list = []

        # find the edge paths for the nodes in node_set
        while node_set:
            # for each node in node_set find other nodes on the path
            intermediates = set()
            popped_node = node_set.pop()
            # intermediates are the nodes in the node_path that are between two other nodes in the path
            intermediates.add(popped_node)
            node_path = {popped_node}
            candidates = {popped_node}
            while candidates:
                popped_cand = candidates.pop()
                # matches are the nodes that belong to a node_path
                matches = edge_dict[popped_cand]
                matches = matches - node_path
                for match in matches:
                    intermediates.add(popped_cand)
                    # if the found node on the path is in the node_set, then keep looking for other connected nodes on
                    # the path
                    if match in node_set:
                        candidates.add(match)
                        node_path.add(match)
                        node_set.remove(match)
                    # If the found node is not in node_set stop.
                    else:
                        node_path.add(match)
            # After finding all nodes on a path find the edges that are connected to these nodes.
            # Finding the edges is different for the nodes in the node path with degree 2 and 4.
            if len(node_path) >= 2:
                if any(node_path.intersection(filtered_degree_4_set)):
                    # node_path has nodes with degree 4 => get the forward and backward paths
                    _edge_paths = find_and_append_degree_4_paths(_edge_paths)
                else:
                    # node_path has nodes with degree 2 => find the edges connected to the intermediates
                    edge_paths_gdf = snkit_network.edges[
                        snkit_network.edges.from_id.isin(intermediates)
                        | snkit_network.edges.to_id.isin(intermediates)
                    ]
                    _edge_paths.append(edge_paths_gdf)
        return _edge_paths

    # Adds degree column which is needed to find the to-be-simplified nodes and edges.
    if "degree" not in snkit_network.nodes.columns:
        snkit_network.nodes["degree"] = snkit_network.nodes[id_col].apply(
            lambda x: node_connectivity_degree(x, snkit_network)
        )

    # Filter on the nodes with degree 2 and 4 which suffice the following criteria:
    # For _node_set with all degree 2: this filters on the nodes that have only one predecessor and successor.
    # E.g. filters on 2 in 1->2, 1->5, 2->3, 3->4, 3->5
    # For _node_set with all degree 4: Check if the predecessors and successors are the same nodes.
    # E.g. filters on 2 in 1->2, 2->3, 2->1, 3->2.
    degree_2_set = set(
        list(snkit_network.nodes[id_col].loc[snkit_network.nodes.degree == 2])
    )
    filtered_degree_2_set = filter_node(degree_2_set, _degrees=2)

    degree_4_set = set(
        list(snkit_network.nodes[id_col].loc[snkit_network.nodes.degree == 4])
    )
    filtered_degree_4_set = filter_node(degree_4_set, _degrees=4)

    nodes_of_interest = filtered_degree_2_set | filtered_degree_4_set

    edge_paths = get_edge_paths(sorted(nodes_of_interest), snkit_network)

    edge_ids_to_update = get_edge_ids_to_update(edge_paths)
    edges_to_keep = snkit_network.edges[
        ~snkit_network.edges["id"].isin(edge_ids_to_update)
    ]

    updated_edges = get_merged_edges(
        paths_to_group=edge_paths, by=by, aggfunc=aggregate_func, net=snkit_network
    )
    edges_to_keep = edges_to_keep.drop(columns=["id"])
    updated_edges = updated_edges.reset_index(drop=True)

    new_edges = pd.concat([edges_to_keep, updated_edges], ignore_index=True)
    new_edges_gdf = gpd.GeoDataFrame(new_edges, geometry="geometry")
    new_edges_gdf.set_crs(edges_to_keep.crs, inplace=True)
    new_edges_gdf = new_edges_gdf.reset_index(drop=True)

    nodes_to_keep = list(set(new_edges.from_id.tolist() + new_edges.to_id.tolist()))
    new_nodes_gdf = snkit_network.nodes[snkit_network.nodes[id_col].isin(nodes_to_keep)]
    new_nodes_gdf = new_nodes_gdf.reset_index(drop=True)

    merged_snkit_network = SnkitNetwork(nodes=new_nodes_gdf, edges=new_edges_gdf)
    merged_snkit_network.nodes["degree"] = merged_snkit_network.nodes[id_col].apply(
        lambda x: node_connectivity_degree(x, merged_snkit_network)
    )

    return merged_snkit_network


def _merge_connected_lines(
    gdf: gpd.GeoDataFrame, by: str, aggfunc: dict
) -> gpd.GeoDataFrame:
    """
    Merge connected lines in a GeoDataFrame into a single LineString.

    Parameters:
    gdf (gpd.GeoDataFrame): GeoDataFrame containing the lines to merge.
    by (str): Column name to group by.
    aggfunc (dict): Dictionary of aggregation functions for other columns.

    Returns:
    gpd.GeoDataFrame: GeoDataFrame with merged lines.
    """

    # Merge all geometries into a single MultiLineString
    merged_geometry = linemerge(gdf.geometry.tolist())
    indices = gdf[by].iloc[0]
    # Create a new GeoDataFrame with the merged geometry
    merged_gdf = gpd.GeoDataFrame(
        [{**indices, "geometry": merged_geometry}], crs=gdf.crs
    )
    merged_gdf.set_index(by, inplace=True)

    # Combine the attributes using the aggregation function
    for col, func in aggfunc.items():
        if col != "geometry":
            # Try to convert the column to float if needed
            if gdf[col].dtype != float:
                try:
                    gdf[col] = gdf[col].astype(float)
                except ValueError:
                    pass  # Skip conversion if it fails
            merged_gdf[col] = [func(gdf[col])]

    return merged_gdf


def _get_merge_edge_paths(
    edges: gpd.GeoDataFrame,
    excluded_edge_types: list,
    aggfunc: str | dict,
    snkit_network: SnkitNetwork,
) -> gpd.GeoDataFrame:
    def get_connected_lines(ids: pd.Index):
        """
        Find groups of connected lines in a GeoDataFrame.

        Parameters:
        gdf (GeoDataFrame): A GeoDataFrame containing LINESTRING geometries.

        Returns:
        list of lists: Each sublist contains indices of lines in gdf that are connected.
        """

        # Initialize an empty graph
        _networkx_graph = nx.Graph()
        gdf = edges.loc[ids.tolist()]
        # Add edges to the graph for each line in the GeoDataFrame
        for idx, row in gdf.iterrows():
            # Get the start and end points of the line
            line = row["geometry"]
            start_point = line.coords[0]
            end_point = line.coords[-1]

            # Add the line as an edge between its start and end points with the id as attribute
            _networkx_graph.add_edge(start_point, end_point, index=idx, id=row["id"])

        # Find connected components in the graph
        connected_components = list(nx.connected_components(_networkx_graph))

        # Map each component to the corresponding line ids
        connected_line_groups = []
        for component in connected_components:
            line_ids = []
            for _, _, data in _networkx_graph.edges(component, data=True):
                line_ids.append(data["id"])
            connected_line_groups.append(line_ids)

        return connected_line_groups

    def _get_paths_to_merge(groups: dict) -> list:
        _paths_to_merge = []  # list of gpds to merge
        for _, edge_group_ids in groups.items():
            sub_path_parts = get_connected_lines(edge_group_ids)
            _paths_to_merge.extend(sub_path_parts)
        return _paths_to_merge

    # _get_merged_paths starts here
    grouped_edges = edges.groupby(excluded_edge_types)
    if len(grouped_edges.groups) == 1:
        merged_edges = GdfSnkitNetworkMerger(
            geo_dataframe=edges, snkit_network=snkit_network
        ).merge(
            by=excluded_edge_types,
            aggregate_func=aggfunc,
        )
    else:
        merged_edges = gpd.GeoDataFrame(
            columns=edges.columns, crs=edges.crs
        )  # merged edges
        edge_groups = edges.groupby(excluded_edge_types).groups
        paths_to_merge = _get_paths_to_merge(edge_groups)

        for path_ids in paths_to_merge:
            path_to_merge = edges[
                edges["id"].isin(path_ids)
            ].copy()  # indices of the edges in edges gdf
            merged = GdfSnkitNetworkMerger(
                geo_dataframe=path_to_merge, snkit_network=snkit_network
            ).merge(
                by=excluded_edge_types,
                aggregate_func=aggfunc,
            )
            merged_edges = pd.concat([merged_edges, merged], ignore_index=True)

        merged_edges.crs = edges.crs

    return merged_edges


class GdfSnkitNetworkMerger:
    """
    Merger of a `gpd.GeoDataFrame` and a `snkit.network.network`.
    This class was created to contain the related close and try reducing the code's complexity.
    """

    def __init__(
        self, geo_dataframe: gpd.GeoDataFrame, snkit_network: SnkitNetwork
    ) -> None:
        self._geo_dataframe = geo_dataframe
        self._snkit_network = snkit_network

    def merge(
        self,
        by: list,
        aggregate_func: dict,
    ) -> gpd.GeoDataFrame:
        """
        Merges the inner defined `gpd.GeoDataFrame` and `snkit.network.Network`
        based on the given arguments (`by`) and aggregation function ()`aggregate_func`).
        """
        _geo_dataframe = self._geo_dataframe
        _snkit_network = self._snkit_network
        # _merge function starts from here:
        self._geo_dataframe["intersections"] = _geo_dataframe.apply(
            lambda x: self._get_intersections(x, _geo_dataframe), axis=1
        )
        # _merged = gdf.dissolve(by=by, aggfunc=_aggfunc, sort=False)
        _merged = _merge_connected_lines(_geo_dataframe, by, aggregate_func)
        if len(_geo_dataframe) == 1:
            # 1. no merging is occurring
            start_path_extremities = [_geo_dataframe.iloc[0]["from_id"]]
            end_path_extremities = [_geo_dataframe.iloc[0]["to_id"]]
            _merged.from_id = start_path_extremities[0]
            _merged.to_id = end_path_extremities[0]
        else:
            # 2. merging is occurring
            if (
                len(
                    _geo_dataframe[
                        _geo_dataframe["intersections"].apply(lambda x: len(x) == 1)
                    ]
                )
                == 0
            ):
                # 2.1. a loop with two nodes degree > 2
                gdf_node_ids = list(
                    set(_geo_dataframe.from_id.tolist() + _geo_dataframe.to_id.tolist())
                )
                gdf_node_slice = _snkit_network.nodes[
                    _snkit_network.nodes["id"].isin(gdf_node_ids)
                ]
                if len(gdf_node_slice[gdf_node_slice["degree"] > 2]) == 0:
                    # 2.1.1. a loop with only degree 2 edges => isolated from the rest of the graph
                    logging.warning(
                        """
                    A sub-graph loop isolated from the main graph is detected and removed.
                    This isolated part had %s nodes with node_fids {gdf_node_slice.id.tolist()} in
                    the input node graph.
                    """,
                        len(gdf_node_slice),
                    )
                    if "demand_edge" in _geo_dataframe.columns:
                        logging.warning(
                            """'This sub-graph had these demand nodes %s""",
                            (
                                _geo_dataframe[
                                    _geo_dataframe.demand_edge == 1
                                ].from_id.tolist()
                                + _geo_dataframe[
                                    _geo_dataframe.demand_edge == 1
                                ].to_id.tolist()
                            ),
                        )
                    return gpd.GeoDataFrame(
                        data=None,
                        columns=_snkit_network.edges.columns,
                        crs=_snkit_network.edges.crs,
                    )

                elif len(gdf_node_slice[gdf_node_slice["degree"] > 2]) == 1:
                    # 2.1.2. If there is only one node with the degree bigger than 2
                    if (
                        "demand_edge" not in _geo_dataframe.columns
                        or len(_geo_dataframe[_geo_dataframe["demand_edge"] == 1]) == 0
                    ):
                        # No demand node is in this loop. Then omit this loop and return empty gdf
                        return gpd.GeoDataFrame(
                            data=None,
                            columns=_snkit_network.edges.columns,
                            crs=_snkit_network.edges.crs,
                        )
                    elif (
                        "demand_edge" in _geo_dataframe.columns
                        and len(_geo_dataframe[_geo_dataframe["demand_edge"] == 1]) > 0
                    ):
                        demand_node_ids = [
                            i
                            for i in set(
                                _geo_dataframe.from_id.tolist()
                                + _geo_dataframe.to_id.tolist()
                            )
                            if (
                                _geo_dataframe[
                                    _geo_dataframe.demand_edge == 1
                                ].from_id.tolist()
                                + _geo_dataframe[
                                    _geo_dataframe.demand_edge == 1
                                ].to_id.tolist()
                            ).count(i)
                            == 2
                        ]
                        if len(demand_node_ids) > 1:
                            # merging this situation is skipped: not probable + complicated
                            return _geo_dataframe
                        else:
                            # Only one demand node exists in the loop
                            if isinstance(
                                linemerge(_merged.geometry.iloc[0]), MultiLineString
                            ):
                                # to exclude the merged geoms for which linemerge does not work
                                return _geo_dataframe
                            path_extremities_node_ids = {
                                x
                                for x in gdf_node_slice[
                                    gdf_node_slice["degree"] > 2
                                ].id.tolist()
                                + demand_node_ids
                            }
                            _merged = self._get_merged_multiple_demand_edges(
                                _merged, path_extremities_node_ids
                            )
                else:
                    # 2.1.3. the only remaining option is two nodes with degrees bigger than 2
                    if (
                        "demand_edge" not in _geo_dataframe.columns
                        or len(_geo_dataframe[_geo_dataframe["demand_edge"] == 1]) == 0
                    ):
                        # No demand node is in this loop. Then merge
                        _merged = self._get_merged_in_a_loop(_merged, gdf_node_slice)
                    else:
                        return _geo_dataframe
            else:
                # 2.2. merging non-loop paths
                path_extremities_node_ids = {
                    i
                    for i in set(
                        _geo_dataframe.from_id.tolist() + _geo_dataframe.to_id.tolist()
                    )
                    if (
                        _geo_dataframe.from_id.tolist() + _geo_dataframe.to_id.tolist()
                    ).count(i)
                    == 1
                }
                # if len(path_extremities_node_ids) > 0:
                if ("demand_edge" in _geo_dataframe.columns) and (
                    len(_geo_dataframe[_geo_dataframe["demand_edge"] == 1]) > 1
                ):
                    _merged = self._get_merged_multiple_demand_edges(
                        _merged, path_extremities_node_ids
                    )
                elif (
                    "demand_edge" in _geo_dataframe.columns
                    and len(_geo_dataframe[_geo_dataframe["demand_edge"] == 1]) <= 1
                ) or ("demand_edge" not in _geo_dataframe.columns):
                    # 2.2.2.no dem node is in the to_be_merged path or only one dem node. In the later case dem node
                    # will not be dissolved because it is in the path_extremities_node_ids
                    _merged = self._get_merged_one_or_none_demand_edges(
                        _merged, path_extremities_node_ids
                    )
                else:
                    raise ValueError(
                        f"""Check the lines with the following ids {_geo_dataframe.id.tolist()} """
                    )

        _merged.node_A = _merged.from_id
        _merged.node_B = _merged.to_id
        _merged.crs = _geo_dataframe.crs
        return _merged

    def _get_merged_in_a_loop(
        self, _merged: gpd.GeoDataFrame, gdf_node_slice: pd.DataFrame
    ) -> gpd.GeoDataFrame:
        # 2.1.2. pick one with one intersection point
        start_path_extrms = [gdf_node_slice[gdf_node_slice["degree"] > 2].iloc[0].id]
        end_path_extrms = [gdf_node_slice[gdf_node_slice["degree"] > 2].iloc[1].id]
        _merged.from_id = [
            start_path_extremity for start_path_extremity in start_path_extrms
        ]
        _merged.to_id = [end_path_extremity for end_path_extremity in end_path_extrms]
        return _merged

    def _get_merged_multiple_demand_edges(
        self, _merged: gpd.GeoDataFrame, path_extrms_nod_ids: set
    ) -> gpd.GeoDataFrame:
        def get_node_id(r: gpd.GeoSeries, attr: str, path_extrms_nod_ids: set) -> int:
            # to fill from_id and to_id of the to-be-merged paths
            if r[attr] == -1:
                for path_extremities_node_id in path_extrms_nod_ids:
                    path_extremities_node_geom = self._snkit_network.nodes[
                        self._snkit_network.nodes.id == path_extremities_node_id
                    ].geometry.iloc[0]
                    if r.geometry.intersects(path_extremities_node_geom):
                        return path_extremities_node_id
            else:
                return r[attr]

        _mrgd = self._get_split_edges_info(_merged)
        _mrgd.from_id = _mrgd.apply(
            lambda row: get_node_id(row, "from_id", path_extrms_nod_ids), axis=1
        )
        _mrgd.to_id = _mrgd.apply(
            lambda row: get_node_id(row, "to_id", path_extrms_nod_ids), axis=1
        )
        return _mrgd

    def _get_split_edges_info(self, merged: gpd.GeoDataFrame) -> tuple:
        # used for the cases where demand nodes exist in the to-be-merged paths
        # make the demand node from_id of the merged edge
        geo_dataframe = self._geo_dataframe
        dem_nod_ids = [
            i
            for i in set(geo_dataframe.from_id.tolist() + geo_dataframe.to_id.tolist())
            if (
                geo_dataframe[geo_dataframe.demand_edge == 1].from_id.tolist()
                + geo_dataframe[geo_dataframe.demand_edge == 1].to_id.tolist()
            ).count(i)
            == 2
        ]
        split_parts = [merged["geometry"].iloc[0]]
        split_edges_gdf = gpd.GeoDataFrame(columns=merged.columns)
        for dem_nod_id in dem_nod_ids:
            for part in split_parts:
                part_splits, split_edges_gdf = self._split(
                    merged, part, dem_nod_id, split_edges_gdf
                )
                if part_splits is not None:
                    split_parts.extend(part_splits)
                    split_parts.remove(part)
        return split_edges_gdf

    def _split(
        self,
        merged: gpd.GeoDataFrame,
        line_geom: MultiLineString | LineString,
        dem_nod_id: int,
        splits_gdf: gpd.GeoDataFrame,
    ) -> tuple:
        # used for the cases where demand nodes exist in the to-be-merged paths
        dem_nod_geom = self._snkit_network.nodes[
            self._snkit_network.nodes.id == dem_nod_id
        ].geometry.iloc[0]
        if line_geom.contains(dem_nod_geom):
            if isinstance(line_geom, MultiLineString):
                coords = [
                    linemerge(line_geom).coords[0],
                    linemerge(line_geom).coords[-1],
                ]
            else:
                coords = [line_geom.coords[0], line_geom.coords[-1]]
            # Add the coords from the points
            coords += dem_nod_geom.coords
            # Calculate the distance along the line for each point
            dists = [linemerge(line_geom).project(Point(p)) for p in coords]
            # sort the coordinates
            coords = [p for (d, p) in sorted(zip(dists, coords))]
            splits = [
                LineString([coords[i], coords[i + 1]]) for i in range(len(coords) - 1)
            ]
            splits_gdf = self._update_split_edges_gdf(
                merged, splits, dem_nod_id, splits_gdf, line_geom
            )
            return splits, splits_gdf
        else:
            return None, splits_gdf

    def _update_split_edges_gdf(
        self,
        merged: gpd.GeoDataFrame,
        parts: list,
        dem_nod_id: int,
        splt_edgs: gpd.GeoDataFrame,
        _split_line_geom: LineString,
    ) -> gpd.GeoDataFrame:
        # used for the cases where demand nodes exist in the to-be-merged paths
        for part in parts:
            # _split_line_geom is the line divided and produced parts
            if _split_line_geom not in splt_edgs.geometry.tolist():
                part_gdf = gpd.GeoDataFrame(
                    {
                        "geometry": part,
                        "id": len(splt_edgs),
                        "from_id": dem_nod_id,
                        "to_id": -1,
                        **merged.drop(columns=["geometry", "id", "from_id", "to_id"]),
                    }
                )
            else:
                # if _split_line_geom is divided and n stored in splt_edgs, we need to retrieve from/to_id info
                # and update splt_edgs
                part_gdf = gpd.GeoDataFrame(
                    {
                        "geometry": part,
                        "id": -1,
                        "from_id": splt_edgs[
                            splt_edgs.geometry == _split_line_geom
                        ].apply(
                            lambda row: (
                                row.from_id if row.from_id != -1 else dem_nod_id
                            ),
                            axis=1,
                        ),
                        "to_id": splt_edgs[
                            splt_edgs.geometry == _split_line_geom
                        ].apply(
                            lambda row: (row.to_id if row.to_id != -1 else dem_nod_id),
                            axis=1,
                        ),
                        **merged.drop(columns=["geometry", "id", "from_id", "to_id"]),
                    }
                )
                _split_line_index = splt_edgs.loc[
                    splt_edgs.geometry == _split_line_geom
                ].index[0]
                splt_edgs = splt_edgs.drop(_split_line_index)
            splt_edgs = pd.concat([splt_edgs, part_gdf], ignore_index=True)
        return splt_edgs

    def _get_merged_one_or_none_demand_edges(
        self, _merged, path_extrms_nod_ids: set
    ) -> gpd.GeoDataFrame:
        geo_dataframe = self._geo_dataframe
        _start_edges = geo_dataframe[
            geo_dataframe["intersections"].apply(lambda x: len(x) == 1)
        ]
        if ("demand_edge" in geo_dataframe.columns) and (
            len(geo_dataframe[geo_dataframe["demand_edge"] == 1])
        ) == 1:
            _start_edge = _start_edges[_start_edges.demand_edge == 1].iloc[0]
        elif ("demand_edge" not in geo_dataframe.columns) or (
            len(geo_dataframe[geo_dataframe["demand_edge"] == 1])
        ) != 1:
            _start_edge = _start_edges.iloc[0]
        start_path_extrms = [
            (
                _start_edge["from_id"]
                if _start_edge["from_id"] in list(path_extrms_nod_ids)
                else _start_edge["to_id"]
            )
        ]
        end_path_extrms = [(path_extrms_nod_ids - set(start_path_extrms)).pop()]
        _merged.from_id = [
            start_path_extremity for start_path_extremity in start_path_extrms
        ]
        _merged.to_id = [end_path_extremity for end_path_extremity in end_path_extrms]
        return _merged

    def _get_intersections(self, _edge, _edges):
        intersections = []
        edge_geometry = _edge.geometry.simplify(tolerance=1e-8)

        for _, other_edge in _edges.iterrows():
            other_edge_geometry = other_edge.geometry.simplify(tolerance=1e-8)

            if not edge_geometry.equals(other_edge_geometry):  # avoid self-intersection
                intersection = edge_geometry.intersection(other_edge_geometry)

                if not intersection.is_empty and any(
                    intersection.intersects(boundary)
                    for boundary in edge_geometry.boundary.geoms
                ):
                    if isinstance(intersection, MultiPoint):
                        intersections.extend(
                            [
                                point.coords[0]
                                for point in intersection.geoms
                                if point in other_edge_geometry.boundary.geoms
                            ]
                        )
                    else:
                        intersections.append(intersection.coords[0])

        return sorted(intersections, key=lambda x: x[0])
