from dataclasses import dataclass

from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from osmnx import graph_to_gdfs, get_nearest_edge, utils_graph, utils
from shapely.geometry import Point

"""
    This is a wrapper for some of the relevant functions of OSMNX package
"""


@dataclass
class OsmnxWrapper:

    def graph_to_gdf(self, graph, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True) -> GeoDataFrame:
        u, v, k, data = zip(*graph.edges(keys=True, data=True))
        graph_gdf = graph_to_gdfs(graph, nodes, edges, node_geometry, fill_edge_geometry)
        graph_gdf["data"] = data
        return graph_gdf

    def get_node_nearest_edge(
            self, graph: MultiDiGraph, node: tuple, return_geom=True, return_dist=True) \
            -> dict[tuple, tuple]:
        # nearest_edge = get_nearest_edge(graph, node, return_geom, return_dist)

        osmnx_wrapper = OsmnxWrapper()
        # get u, v, key, geom from all the graph edges
        gdf_edges = osmnx_wrapper.graph_to_gdf(graph, nodes=False, fill_edge_geometry=True)
        edges = gdf_edges[["u", "v", "data", "key", "geometry"]].values

        # convert lat,lng (y,x) node to x,y for shapely distance operation
        xy_point = Point(reversed(node))

        # calculate euclidean distance from each edge's geometry to this node
        edge_distances = [(edge, xy_point.distance(edge[4])) for edge in edges]

        # the nearest edge minimizes the distance to the node
        (u, v, data, key, geom), dist = min(edge_distances, key=lambda x: x[1])
        utils.log(f"Found nearest edge ({u, v, data, key}) to node {node}")

        # return results requested by caller
        if data == 0 and key == 0:
            if return_dist and return_geom:
                return {node: (u, v, geom, dist)}
            elif return_dist:
                return {node: (u, v, dist)}
            elif return_geom:
                return {node: (u, v, geom)}
            else:
                return {node: (u, v)}
        elif data == 0:
            if return_dist and return_geom:
                return {node: (u, v, key, geom, dist)}
            elif return_dist:
                return {node: (u, v, key, dist)}
            elif return_geom:
                return {node: (u, v, key, geom)}
            else:
                return {node: (u, v, key)}
        elif key == 0:
            if return_dist and return_geom:
                return {node: (u, v, data, geom, dist)}
            elif return_dist:
                return {node: (u, v, data, dist)}
            elif return_geom:
                return {node: (u, v, data, geom)}
            else:
                return {node: (u, v, data)}
        else:
            if return_dist and return_geom:
                return {node: (u, v, data, key, geom, dist)}
            elif return_dist:
                return {node: (u, v, data, key, dist)}
            elif return_geom:
                return {node: (u, v, data, key, geom)}
            else:
                return {node: (u, v, data, key)}
