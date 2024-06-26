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
from pathlib import Path
from typing import Optional

import geopandas as gpd
import networkx as nx
import numpy as np
from geopandas import GeoDataFrame
from osmnx import graph_to_gdfs
from shapely.geometry import LineString, Point

from ra2ce.network import networks_utils as nut


def from_shapefile_to_poly(shapefile: Path, out_path: Path, outname: str = ""):
    """
    This function will create the .poly files from an input shapefile.
    If the shapefile contains multiple polygons, this function creates a seperate .polygon file for each region
    .poly files can then be used to extract data from the openstreetmap files.

    This function is adapted from the OSMPoly function in QGIS, and Elco Koks GMTRA model.
    This code is maintained on a GitHub repository: github.com/keesvanginkel/OSdaMage

    Arguments:
        *shapefile* (string/Pathlib Path) : path to the shapefile
        *out_path* (string/Pathlib Path): path to the directory where the .poly files should be written
        *outname* (string) : optional prefix to add to outfile name

    Returns:
        .poly file for each region, in a new dir in the working directory (in the CRS of te input file)
    """
    shp_file_gdf = gpd.read_file(str(shapefile), engine="pyogrio")

    num = 0
    # iterate over the seperate polygons in the shapefile
    for f in shp_file_gdf.iterrows():
        f = f[1]
        num = num + 1
        geom = f.geometry

        try:
            # this will create a list of the different subpolygons
            if geom.geom_type == "MultiPolygon":
                polygons = geom

            # the list will be length 1 if it is just one polygon
            elif geom.geom_type == "Polygon":
                polygons = [geom]

            # define the name of the output file
            id_name = str(f.name)

            # start writing the .poly file
            _poly_filename = out_path / (outname + id_name + ".poly")
            with open(_poly_filename, "w") as _poly_file:
                _poly_file.write(id_name + "\n")
                i = 0

                # loop over the different polygons, get their exterior and write the
                # coordinates of the ring to the .poly file
                for polygon in polygons:
                    polygon = np.array(polygon.exterior)

                    j = 0
                    _poly_file.write(str(i) + "\n")

                    for ring in polygon:
                        j = j + 1
                        _poly_file.write(
                            "    " + str(ring[0]) + "     " + str(ring[1]) + "\n"
                        )

                    i = i + 1
                    # close the ring of one subpolygon if done
                    _poly_file.write("END" + "\n")

                # close the file when done
                _poly_file.write("END" + "\n")
        except Exception as e:
            print("Exception {}".format(e))


def graph_to_gdf(
    graph: nx.Graph,
    nodes: bool,
    edges: bool,
    node_geometry: bool,
    fill_edge_geometry: bool,
) -> GeoDataFrame:
    u, v, k, data = zip(*graph.edges(keys=True, data=True))
    graph_gdf = graph_to_gdfs(graph, nodes, edges, node_geometry, fill_edge_geometry)
    graph_gdf["data"] = data
    return graph_gdf


def get_node_nearest_edge(
    graph: nx.MultiDiGraph, node: tuple, return_geom=True, return_dist=True
) -> dict:
    """
    Based on osmnx.
    """
    node_coor = (node[1]["x"], node[1]["y"])
    # get u, v, key, geom from all the graph edges
    gdf_edges = graph_to_gdf(
        graph, nodes=False, edges=True, node_geometry=True, fill_edge_geometry=True
    )
    if {"u", "v", "key"}.issubset(gdf_edges.index.names):
        gdf_edges.reset_index(inplace=True)
    edges = gdf_edges[["u", "v", "data", "key", "geometry"]].values

    # convert lat,lng (y,x) node to x,y for shapely distance operation
    xy_point = Point(node_coor)

    # calculate Euclidean distance from each edge's geometry to this node
    edge_distances = [(edge, xy_point.distance(edge[4])) for edge in edges]

    # the nearest edge minimizes the non-zero distance to the node
    (u, v, data, key, geom), dist = min(
        edge_distances, key=lambda x: x[1] if x[1] > 0 else float("inf")
    )
    logging.info(f"Found nearest edge ({u, v, data, key}) to node {node}")

    # return results requested by caller
    if data == 0 and key == 0:
        if return_dist and return_geom:
            return {"node": node, "nearest_edge": (u, v, geom, round(dist, 7))}
        elif return_dist:
            return {"node": node, "nearest_edge": (u, v, round(dist, 7))}
        elif return_geom:
            return {"node": node, "nearest_edge": (u, v, geom)}
        else:
            return {"node": node, "nearest_edge": (u, v)}
    elif data == 0:
        if return_dist and return_geom:
            return {"node": node, "nearest_edge": (u, v, key, geom, round(dist, 7))}
        elif return_dist:
            return {"node": node, "nearest_edge": (u, v, key, round(dist, 7))}
        elif return_geom:
            return {"node": node, "nearest_edge": (u, v, key, geom)}
        else:
            return {"node": node, "nearest_edge": (u, v, key)}
    elif key == 0:
        if return_dist and return_geom:
            return {"node": node, "nearest_edge": (u, v, data, geom, round(dist, 7))}
        elif return_dist:
            return {"node": node, "nearest_edge": (u, v, data, round(dist, 7))}
        elif return_geom:
            return {"node": node, "nearest_edge": (u, v, data, geom)}
        else:
            return {"node": node, "nearest_edge": (u, v, data)}
    else:
        if return_dist and return_geom:
            return {
                "node": node,
                "nearest_edge": (u, v, data, key, geom, round(dist, 7)),
            }
        elif return_dist:
            return {"node": node, "nearest_edge": (u, v, data, key, round(dist, 7))}
        elif return_geom:
            return {"node": node, "nearest_edge": (u, v, data, key, geom)}
        else:
            return {"node": node, "nearest_edge": (u, v, data, key)}


def is_endnode_check(graph: nx.MultiDiGraph, node_id: int) -> bool:
    """
    Based on osmnx. osmnx rules 3 and 4 are removed. Hence, the name is_endpoint_simplified.
    Determine if a node is a true endpoint of an edge.

    Return True if the node is a "true" endpoint of an edge in the network,
    otherwise False. OpenStreetMap's data includes many nodes that exist only as
    geometric vertices to allow ways to curve. A true edge endpoint is a node
    that satisfies at least 1 of the following 4 rules:

    1) It is its own neighbor (ie, it self-loops).

    2) Or, it has no incoming edges or no outgoing edges (ie, all its incident
    edges are inbound or all its incident edges are outbound).

    graph : networkx.MultiDiGraph input graph
    node_id : int the node to examine
    """
    neighbors = set(list(graph.predecessors(node_id)) + list(graph.successors(node_id)))
    # rule 1
    if node_id in neighbors:
        # if the node appears in its list of neighbors, it self-loops
        # this is always an endpoint.
        return True

    # rule 2
    elif graph.out_degree(node_id) == 0 or graph.in_degree(node_id) == 0:
        # if node has no incoming edges or no outgoing edges, it is an endpoint
        return True
    else:
        return False


def create_edges(
    graph: nx.MultiDiGraph, u: int, v: int, key_data: dict
) -> nx.MultiDiGraph:
    """
    Create or update edges between nodes `u` and `v` in the graph with the given data.

    Args:
        graph (nx.MultiDiGraph): The graph to modify.
        u (int): The ID of the source node.
        v (int): The ID of the target node.
        data (dict): The attributes for the new edge(s).

    Returns:
        nx.MultiDiGraph: The modified graph.
    """
    # Ensure all keys in data are strings
    for key, data in key_data.items():
        if not graph.has_edge(u, v, key):
            geom_data = {
                "geometry": LineString(
                    [
                        graph.nodes(data=True)[u]["geometry"],
                        graph.nodes(data=True)[v]["geometry"],
                    ]
                )
            }
            graph.add_edge(u, v, **data)
            graph[u][v][key].update(geom_data)
    return graph


def update_edges_by_node(
    graph: nx.MultiDiGraph, node_edges: list, node_id: int, new_node_geom: dict
) -> None:
    """
    Update connected edges of a node by replacing node_id and node_geom with new_node_id and new_node_geom.

    Args:
        node_edges: edges connected to the node in teh original graph to modify
        graph (nx.MultiDiGraph): The graph to modify.
        node_id (int): The ID of the node to update.
        new_node_geom (dict): Dictionary containing geometry information for the new node.

    Returns:
        None
    """
    # Iterate over connected edges
    for u, v, key, existing_edge_data in node_edges:
        # Step 0: Save existing edge data (excluding geometry and length)
        new_edge_data = existing_edge_data.copy()
        # Step 1: Determine if node_id is a u or v in the edge
        if u == node_id:
            new_edge_id = (node_id, v, key)
            new_line_points = LineString(
                [new_node_geom, graph.nodes(data=True)[v]["geometry"]]
            )
        elif v == node_id:
            new_edge_id = (u, node_id, key)
            new_line_points = LineString(
                [graph.nodes(data=True)[u]["geometry"]], new_node_geom
            )

        # Step 2: Set attributes of the new edge using existing edge data and
        # Set geometry and length of the new edge
        new_edge_data.update(
            {
                "geometry": LineString(new_line_points),
                "length": nut.line_length(
                    LineString(new_line_points), graph.graph["crs"]
                ),
            }
        )

        # Step 3: Create a new edge by replacing node_id with new_node_id
        graph.add_edge(*new_edge_id, **new_edge_data)


def modify_graph(graph: nx.MultiDiGraph, node_nearest_edge_data: dict):
    def set_edge_length(
        graph: nx.MultiDiGraph, u_nearest_edge: int, v_nearest_edge, new_node_id
    ):
        for _, nodes in enumerate(
            [(u_nearest_edge, new_node_id), (new_node_id, v_nearest_edge)], start=1
        ):
            u, v = nodes
            for key in graph[u][v]:
                length_data = {
                    "length": nut.line_length(
                        graph[u][v][key]["geometry"], graph.graph["crs"]
                    )
                }
                graph[u][v][key].update(length_data)

    def get_edges_by_node(graph, node):
        return list(graph.edges(node, data=True, keys=True))

    # step 1: set variables
    u_nearest_edge = node_nearest_edge_data["nearest_edge"][0]
    v_nearest_edge = node_nearest_edge_data["nearest_edge"][1]
    nearest_edge_geom = node_nearest_edge_data["nearest_edge"][3]
    nearest_edge_key_data = graph.get_edge_data(u_nearest_edge, v_nearest_edge).copy()
    if nearest_edge_key_data is None:
        raise ValueError("Edge not found in the graph")

    node_id = node_nearest_edge_data["node"][0]
    node_geom = node_nearest_edge_data["node"][1]["geometry"]
    node_edges = get_edges_by_node(graph, node_id).copy()

    new_node_geom = nearest_edge_geom.interpolate(nearest_edge_geom.project(node_geom))
    new_node_data = node_nearest_edge_data["node"][1].copy()
    new_node_data = remove_key(new_node_data, ["geometry", "x", "y"])

    # step 2: add the new_node
    # Check if the new_node already exists in the nodes of the graph
    if find_existing_node(graph, new_node_geom)[0] is None:
        graph.remove_node(node_id)
        graph.add_node(
            node_id,
            x=new_node_geom.x,
            y=new_node_geom.y,
            geometry=new_node_geom,
            **new_node_data,
        )
    else:
        node_id = find_existing_node(graph, new_node_geom)[0]

    # step 3: update edges of the graph being affected by adding a new node
    graph.remove_edge(u_nearest_edge, v_nearest_edge)
    # Add new node to the nearest edge and create two edges
    graph = create_edges(graph, u_nearest_edge, node_id, nearest_edge_key_data)
    graph = create_edges(graph, node_id, v_nearest_edge, nearest_edge_key_data)
    # update the length of the created edges on the nearest_edge
    set_edge_length(graph, u_nearest_edge, v_nearest_edge, node_id)

    # update edges connected to the node close enough (passed the threshold) to the nearest edge
    update_edges_by_node(graph, node_edges, node_id, new_node_geom)


def remove_key(element_data: dict, keys_to_exclude: list) -> dict:
    """
    Removes keys such as geometry information from the new node data to be created
    Args:
        element_data: dict, node or edge data of a nx.Graph object
        keys_to_exclude: list, information key to exclude from the element_data

    Returns: dict, filtered element_data for the new node or edge to be created in a new nx.Graph object

    """

    for key in keys_to_exclude:
        element_data.pop(key)
    return element_data


def find_existing_node(
    graph: nx.MultiDiGraph, new_node: Point
) -> tuple[int, dict] | tuple[None, None]:
    """
    finds whether a newly created node exists in a graph
    Args:
        graph: nx.MultiDiGraph
        new_node: Shapely Point, a newly created node

    Returns: None if a newly created node does not exist in a graph. Otherwise, returns the node and its data

    """
    for node, data in graph.nodes(data=True):
        if not data.get("geometry", ""):
            raise ValueError("Nodes should have geometry")

        if data["geometry"] == new_node:
            return node, data
    return None, None


def create_edge(graph: nx.MultiDiGraph, u: int, v: int, data: dict) -> nx.MultiDiGraph:
    """
    creates an edge if it does not already exist.
    Args:
        graph: nx.MultiDiGraph
        u: int, starting node of an edge
        v: int, ending node of an edge

    Returns: updated/existing graph containing a new edge

    """
    if graph.has_edge(u, v):
        return graph
    else:
        graph.add_edge(u, v, **data[0])
        return graph
