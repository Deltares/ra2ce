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
import os
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pyproj
import rasterio
import rasterio.mask
import rasterio.transform
from rasterio import Affine
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely.geometry import LineString, Point
from tqdm import tqdm

from ra2ce.network.networks_utils import cut, line_length

"""
TODO: This whole file should be throughouly tested / redesigned.
"""


def read_origin_destination_files(
    origin_paths: Union[str, list],
    origin_names: Union[str, list],
    destination_paths: Union[str, list],
    destination_names: Union[str, list],
    od_id: str,
    origin_count: str,
    crs_: pyproj.CRS,
    category: str,
    region_paths: Optional[str],
    region_var: Optional[str],
):
    """Reads the Origin and Destination point shapefiles and creates one big OD GeoDataFrame.
    Args:
        origin_paths: The path (as string) or paths (in a list) of the point shapefile(s) used for the locations of the Origins.
        origin_names: The name(s) of the origins
        destination_paths: The path (as string) or paths (in a list) of the point shapefile(s) used for the locations of the Destinations.
        destination_names: The name(s) of the destinations
        od_id: The name of the unique identifier attribute in both the origin and destination shapefiles.
        origin_count: The name of the attribute in the origin shapefile that can be used for counting the flow over the network (e.g. nr. of people)
        crs_: The Coordinate Reference System used in the project.
        category: The name of the attribute in the destination shapefile that can be used to categorize the (closest) destination.
        region_paths:
        region_var:
    Returns:
        od:
    """

    if region_paths:
        origin = gpd.GeoDataFrame(
            columns=[od_id, "o_id", "geometry", "region"], crs=crs_
        )
        region = gpd.read_file(region_paths, engine="pyogrio")
        region = region[[region_var, "geometry"]]
    else:
        origin = gpd.GeoDataFrame(columns=[od_id, "o_id", "geometry"], crs=crs_)

    destination_columns = [od_id, "d_id", "geometry"]
    if category:
        destination_columns.append(category)

    destination = gpd.GeoDataFrame(columns=destination_columns, crs=crs_)

    if isinstance(origin_paths, str):
        origin_paths = [origin_paths]
    if isinstance(destination_paths, str):
        destination_paths = [destination_paths]
    if isinstance(origin_names, str):
        origin_names = [origin_names]
    if isinstance(destination_names, str):
        destination_names = [destination_names]

    for op, on in zip(origin_paths, origin_names):
        origin_new = gpd.read_file(op, crs=crs_, engine="pyogrio")
        if od_id not in origin_new.columns:
            logging.warning(
                "No origin found at %s for %s, using default index instead.".format(
                    op, od_id
                )
            )
            origin_new[od_id] = origin_new.index

        if region_paths:
            origin_new = gpd.sjoin(left_df=origin_new, right_df=region, how="left")
            origin_new["region"] = origin_new[region_var]
            origin_new = origin_new[[od_id, origin_count, "geometry", "region"]]
            origin_new["region"].fillna("Not assigned", inplace=True)
        else:
            origin_new = origin_new[[od_id, origin_count, "geometry"]]
        origin_new["o_id"] = on + "_" + origin_new[od_id].astype(str)
        origin_new.crs = origin.crs
        origin = gpd.GeoDataFrame(pd.concat([origin, origin_new], ignore_index=True))

    destination_columns_add = [od_id, "geometry"]
    if category:
        destination_columns_add.append(category)

    for dp, dn in zip(destination_paths, destination_names):
        destination_new = gpd.read_file(dp, crs=crs_, engine="pyogrio")
        if od_id not in destination_new.columns:
            logging.warning(
                "No destination found at %s for %s, using default index instead.".format(
                    dp, od_id
                )
            )
            destination_new[od_id] = destination_new.index
        destination_new = destination_new[destination_columns_add]
        destination_new["d_id"] = dn + "_" + destination_new[od_id].astype(str)
        destination_new.crs = destination.crs
        destination = gpd.GeoDataFrame(
            pd.concat([destination, destination_new], ignore_index=True)
        )

    od = pd.concat([origin, destination], sort=False)

    return od


def closest_node(node: np.ndarray, nodes: np.ndarray) -> np.ndarray:
    deltas = nodes - node
    dist_2 = np.einsum("ij,ij->i", deltas, deltas)
    # Find indices of all minimum distances
    min_dist_indices = np.where(dist_2 == dist_2.min())[0]

    # CROSSCADE: The previous return value `nodes[np.argmin(dist_2)]`
    # returned a np.ndarray of 1 dimension (`[result]`), whilst the new value
    # will return a 2 dimensional np.ndarray ( `[[result]]`)
    return np.round(nodes[min_dist_indices], decimals=7)[0]


def get_od(o_id: str, d_id: str) -> str:
    """
    Gets a valid origin id node from the given pair.

    Args:
        o_id (str): Id for the `origin` node.
        d_id (str): Id for the `destination` node.

    Returns:
        str | np.nan: Valid value to represent the origin - destination node.
    """
    _nan_values = ["nan", np.nan]
    if o_id not in _nan_values:
        return o_id
    if d_id not in _nan_values:
        # `o_id` was nan, so it was a destination, not an origin.
        # therefore we return `d_id`
        return d_id
    return np.nan


def add_data_to_existing_node(graph, node, match_name):
    if "od_id" in graph.nodes[node]:
        # the node already has a origin/destination attribute
        if match_name not in set(graph.nodes[node]["od_id"].split(",")):
            graph.nodes[node]["od_id"] = graph.nodes[node]["od_id"] + "," + match_name
    else:
        graph.nodes[node]["od_id"] = match_name
    return graph


def update_edges_with_new_node(
    graph: nx.MultiGraph,
    edge_data: dict,
    node_a: int,
    node_b: int,
    k: int,
    line_a: LineString,
    line_b: LineString,
    new_node_id: int,
    graph_crs: pyproj.CRS,
    inverse_vertices_dict: dict,
):
    # Check which line is connected to which node. There can be 8 different combinations and there should be two
    # edges added to the graph.
    cnt = 0

    if Point(graph.nodes[node_a]["geometry"].coords[0]).almost_equals(
        Point(line_b.coords[-1])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_b != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_b, graph_crs),
            geometry=line_b,
            node_A=node_a,
            node_B=new_node_id,
            edge_fid=f"{node_a}_{new_node_id}",
        )
        graph.add_edge(node_a, new_node_id, k_new, **edge_data)

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_a, new_node_id, k_new) for p in set(list(line_b.coords[1:-1]))}
        )

        cnt += 1

    if Point(graph.nodes[node_b]["geometry"].coords[0]).almost_equals(
        Point(line_b.coords[0])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_b != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_b, graph_crs),
            geometry=line_b,
            node_A=new_node_id,
            node_B=node_b,
            edge_fid=f"{new_node_id}_{node_b}",
        )
        graph.add_edge(
            new_node_id, node_b, k_new, **edge_data
        )  # changed the u, v order

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_b, new_node_id, k_new) for p in set(list(line_b.coords[1:-1]))}
        )

        cnt += 1

    if Point(graph.nodes[node_a]["geometry"].coords[0]).almost_equals(
        Point(line_b.coords[0])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_b != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_b, graph_crs),
            geometry=line_b,
            node_A=node_a,
            node_B=new_node_id,
            edge_fid=f"{node_b}_{new_node_id}",
        )
        graph.add_edge(node_a, new_node_id, k_new, **edge_data)

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_a, new_node_id, k_new) for p in set(list(line_b.coords[1:-1]))}
        )

        cnt += 1

    if Point(graph.nodes[node_b]["geometry"].coords[0]).almost_equals(
        Point(line_b.coords[-1])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_b != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_b, graph_crs),
            geometry=line_b,
            node_A=new_node_id,
            node_B=node_b,
            edge_fid=f"{new_node_id}_{node_b}",
        )
        graph.add_edge(
            new_node_id, node_b, k_new, **edge_data
        )  # changed the u, v order

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_b, new_node_id, k_new) for p in set(list(line_b.coords[1:-1]))}
        )

        cnt += 1

    if Point(graph.nodes[node_b]["geometry"].coords[0]).almost_equals(
        Point(line_a.coords[0])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_a != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_a, graph_crs),
            geometry=line_a,
            node_A=new_node_id,
            node_B=node_b,
            edge_fid=f"{new_node_id}_{node_b}",
        )
        graph.add_edge(
            new_node_id, node_b, k_new, **edge_data
        )  # changed the u, v order

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_b, new_node_id, k_new) for p in set(list(line_a.coords[1:-1]))}
        )

        cnt += 1

    if Point(graph.nodes[node_a]["geometry"].coords[0]).almost_equals(
        Point(line_a.coords[-1])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_a != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_a, graph_crs),
            geometry=line_a,
            node_A=node_a,
            node_B=new_node_id,
            edge_fid=f"{node_a}_{new_node_id}",
        )
        graph.add_edge(node_a, new_node_id, k_new, **edge_data)

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_a, new_node_id, k_new) for p in set(list(line_a.coords[1:-1]))}
        )

        cnt += 1

    if Point(graph.nodes[node_b]["geometry"].coords[0]).almost_equals(
        Point(line_a.coords[-1])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_a != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_a, graph_crs),
            geometry=line_a,
            node_A=new_node_id,
            node_B=node_b,
            edge_fid=f"{new_node_id}_{node_b}",
        )
        graph.add_edge(
            new_node_id, node_b, k_new, **edge_data
        )  # changed the u, v order

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_b, new_node_id, k_new) for p in set(list(line_a.coords[1:-1]))}
        )

        cnt += 1

    if Point(graph.nodes[node_a]["geometry"].coords[0]).almost_equals(
        Point(line_a.coords[0])
    ):
        if node_a == node_b and graph.has_edge(*(node_a, new_node_id, 0)):
            if line_a != graph.edges[(node_a, new_node_id, 0)]["geometry"]:
                k_new = 1
            else:
                k_new = 0
        else:
            k_new = 0
        edge_data.update(
            length=line_length(line_a, graph_crs),
            geometry=line_a,
            node_A=node_a,
            node_B=new_node_id,
            edge_fid=f"{node_a}_{new_node_id}",
        )
        graph.add_edge(node_a, new_node_id, k_new, **edge_data)

        # Update the inverse vertices dict
        inverse_vertices_dict.update(
            {p: (node_a, new_node_id, k_new) for p in set(list(line_a.coords[1:-1]))}
        )

        cnt += 1

    try:
        assert cnt == 2
    except AssertionError:
        logging.warning(
            "No combination of nodes/road segments found for the OD assignment."
        )

    if graph.has_edge(node_a, node_b, k):
        # remove the edge that is split in two from the graph
        graph.remove_edge(node_a, node_b, k)

    return graph, inverse_vertices_dict


def add_od_nodes(
    od: gpd.GeoDataFrame,
    graph: nx.Graph,
    crs,
    category: Optional[str] = None,
):
    def find_closest_node(
        closest_node_on_road: np.ndarray,
        inverse_vertices_dict: dict,
        inverse_nodes_dict: dict,
        graph: nx.Graph,
    ) -> dict[tuple[float, float], int]:
        closest_u_v_k = inverse_vertices_dict.get(
            (closest_node_on_road[0], closest_node_on_road[1]), None
        )
        if closest_u_v_k:
            closest_u_data = graph.nodes[closest_u_v_k[0]]
            closest_v_data = graph.nodes[closest_u_v_k[1]]
            closest_node_on_extremities = closest_node(
                np.array((closest_node_on_road[0], closest_node_on_road[1])),
                np.array(
                    [
                        [closest_u_data["x"], closest_u_data["y"]],
                        [closest_v_data["x"], closest_v_data["y"]],
                    ]
                ),
            )
            closest_node_on_extremities_id = get_node_id_from_position(
                graph, *closest_node_on_extremities
            )
            inverse_nodes_dict[
                (closest_node_on_road[0], closest_node_on_road[1])
            ] = closest_node_on_extremities_id

        return inverse_nodes_dict

    def get_node_id_from_position(
        g: nx.Graph, x: float, y: float
    ) -> Union[float, None]:
        nodes = [
            (node, data)
            for node, data in g.nodes(data=True)
            if "geometry" in data
            and round(data["geometry"].x, 7) == round(x, 7)
            and round(data["geometry"].y, 7) == round(y, 7)
        ]
        return nodes[0][0] if nodes else None

    """Gets from each origin and destination the closest vertex on the graph edge.
    Args:
        od [Geodataframe]: The GeoDataFrame with the origins and destinations
        graph [networkX graph]: networkX graph
        crs [string or pyproj crs]:
    Returns:
        od [Geodataframe]: The GeoDataFrame with the locations of the origins and destinations on the road vertices
        graph [networkX graph]: The networkX graph updated with origins and destinations
    """
    logging.info("Finding vertices closest to Origins and Destinations")

    # create dictionary of the roads geometries and identifyers
    edge_list = [e for e in graph.edges.data(keys=True) if "geometry" in e[-1]]
    inverse_vertices_dict = {}
    all_vertices = []
    checked_lines = set()
    for line in edge_list:
        # Convert LineString to a hashable type (tuple) for set lookup
        geometry_coords = line[-1]["geometry"].coords
        coords = tuple(sorted([coord for coord in geometry_coords]))
        if coords in checked_lines:
            graph.remove_edge(*line[0:3])
        else:
            inverse_vertices_dict.update(
                {p: (line[0], line[1], line[2]) for p in set(geometry_coords[1:-1])}
            )
            all_vertices.extend(set(geometry_coords))
            checked_lines.add(coords)

    # Make an array from the list
    all_vertices = np.array(all_vertices)

    # Also create an inverse nodes dict of the node geometries as keys and node ID's as values
    inverse_nodes_dict = {
        node[-1]["geometry"].coords[0]: node[0] for node in graph.nodes.data()
    }

    # Get the maximum node id
    max_node_id = max([n for n in graph.nodes()])
    od_list = []
    for i, od_data in tqdm(
        enumerate(
            list(zip(od["geometry"].x, od["geometry"].y, od["o_id"], od["d_id"]))
        ),
        desc="Adding Origin-Destination nodes to graph",
    ):
        match_name = get_od(od_data[-2], od_data[-1])

        # Find the vertex on the road that is closest to the origin or destination point
        closest_node_on_road = closest_node(
            np.array((od_data[0], od_data[1])), all_vertices
        )
        match_od = Point(closest_node_on_road)
        # Find the road to which this vertex belongs. If the vertex is on an end-point of a road, it cannot be found,
        # and it goes to the except statement.
        try:
            closest_u_v_k = inverse_vertices_dict[
                (closest_node_on_road[0], closest_node_on_road[1])
            ]
            match_edge = graph.edges[closest_u_v_k]

            # Add the node to the graph edge
            match_geom = match_edge["geometry"]

            new_lines = split_line_with_points(match_geom, [match_od])
            if len(new_lines) == 1:
                inverse_nodes_dict = find_closest_node(
                    closest_node_on_road,
                    inverse_vertices_dict,
                    inverse_nodes_dict,
                    graph,
                )

            assert len(new_lines) == 2
            assert len([match_od]) == 1

            line1, line2 = new_lines

            new_node_id = max_node_id + 1
            max_node_id = new_node_id

            node_info = {
                "node_fid": new_node_id,  # Check if this attribute always exists
                "y": match_od.coords[0][1],
                "x": match_od.coords[0][0],
                "geometry": match_od,
                "od_id": match_name,
            }
            if category and od_data[-1] == od_data[-1]:
                # If the user wants to calculate the routes to multiple locations with categories
                # and if the current location is a destination (od_data[-1] is not NaN)
                node_info["category"] = od.iloc[i][category]

            # Add the new node to the graph
            graph.add_node(new_node_id, **node_info)

            # Update the inverse_nodes_dict with the new node
            inverse_nodes_dict[match_od.coords[0]] = new_node_id

            # Delete the new node from the inverse_vertices_dict as no end-points are included here
            del inverse_vertices_dict[match_od.coords[0]]

            # Update the graph edges and the inverse_vertices_dict
            graph, inverse_vertices_dict = update_edges_with_new_node(
                graph,
                match_edge,
                closest_u_v_k[0],
                closest_u_v_k[1],
                closest_u_v_k[2],
                line1,
                line2,
                new_node_id,
                crs,
                inverse_vertices_dict,
            )

        except (KeyError, AssertionError):
            # If the vertex is at the end of the road it won't be found in the inverse_vertices_dict,
            # so search in the inverse_nodes_dict.
            match_node = inverse_nodes_dict[
                (closest_node_on_road[0], closest_node_on_road[1])
            ]

            # Update the node with the OD attribute
            graph = add_data_to_existing_node(graph, match_node, match_name)

            if category and od_data[-1] == od_data[-1]:
                # If the user wants to calculate the routes to multiple locations with categories
                # and if the current location is a destination (od_data[-1] is not NaN)
                graph.nodes[match_node]["category"] = od.iloc[i][category]

        # Save both in lists
        od_list.append(match_od)  # save the point as a Shapely Point

    # save in dataframe
    od["OD"] = od_list

    # save the road vertices closest to the origin/destination as geometry, delete the input origin/destination point geometry
    od = gpd.GeoDataFrame(od)
    od = od.drop(columns=["OD"])

    return od, graph


def split_line_with_points(line, points):
    """Splits a line string in several segments considering a list of points."""
    segments = []
    current_line = line

    # make a list of points and its distance to the start to sort them from small to large distance
    list_dist = [current_line.project(pnt) for pnt in points]
    list_dist.sort()

    for d in list_dist:
        # cut the line at a distance d
        seg, current_line = cut(current_line, d)
        if seg:
            segments.append(seg)
    segments.append(current_line)
    return segments


#########################################################################################
################### Code to generate origins points from raster #########################
#########################################################################################


def rescale_and_crop(path_name, gdf, output_folder: Path, res: int = 500):
    dst_crs = rasterio.crs.CRS.from_dict(gdf.crs.to_dict())

    # Rescale and reproject raster to gdf crs
    _output_origins_raster_tif = output_folder / "origins_raster_reprojected.tif"

    with rasterio.open(path_name) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        m2degree = (
            1 / 111000
        )  # approximate conversion from meter to 1 degree of EPSG:4326; TODO: make flexible depending on the input crs
        transform = Affine(
            res * m2degree,
            transform.b,
            transform.c,
            transform.d,
            -res * m2degree,
            transform.f,
        )

        # use scale, instead of absolute meter, for resolution
        # scale = 2
        # transform = Affine(transform.a * scale, transform.b, transform.c, transform.d, transform.e * scale, transform.f)
        # height = height * scale
        # width = width * scale

        kwargs = src.meta.copy()
        kwargs.update(
            {"crs": dst_crs, "transform": transform, "width": width, "height": height}
        )

        with rasterio.open(_output_origins_raster_tif, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.sum,
                )  # Resampling.sum or Resampling.nearest

    raster = rasterio.open(_output_origins_raster_tif)

    # Crop to shapefile
    out_array, out_trans = rasterio.mask.mask(
        dataset=raster, shapes=gdf.geometry, crop=True
    )

    out_meta = raster.meta.copy()
    out_meta.update(
        {
            "height": out_array.shape[1],
            "width": out_array.shape[2],
            "transform": out_trans,
        }
    )
    raster.close()
    os.remove(_output_origins_raster_tif)

    return out_array, out_meta


def export_raster_to_geotiff(array, meta, dir_path: Path, filename: str) -> Path:
    cropped_outputfile = dir_path / filename
    with rasterio.open(
        cropped_outputfile, "w", **meta, compress="LZW", tiled=True
    ) as dest:
        dest.write(array)
    return cropped_outputfile


def generate_points_from_raster(fn, out_fn):
    # Read raster coordinate centroid
    with rasterio.open(fn) as src:
        points = []
        for col in range(src.width):
            x_s, y_s = rasterio.transform.xy(
                src.transform,
                [row for row in range(src.height)],
                [col for _ in range(src.height)],
            )
            points += [Point(x, y) for x, y in zip(x_s, y_s)]

    # Put raster coordinates into geodataframe
    gdf = gpd.GeoDataFrame()
    gdf["geometry"] = points
    gdf["OBJECTID"] = [x for x in range(len(gdf))]

    # Get raster values
    temp = [gdf["geometry"].x, gdf["geometry"].y]
    coords = list(map(list, zip(*temp)))
    with rasterio.open(fn) as src:
        gdf.crs = src.crs
        gdf["values"] = [sample[0] for sample in src.sample(coords)]

    # Save non-zero cells
    gdf.loc[gdf["values"] > 0].to_file(out_fn)

    return out_fn


def origins_from_raster(output_folder: Path, mask_fn, raster_fn) -> Path:
    """Makes origin points from a population raster."""
    output_fn = output_folder / "origins_raster.tif"
    mask = gpd.read_file(mask_fn[0], engine="pyogrio")
    res = 1000  # in meter; TODO: put in config file or in network.ini
    out_array, out_meta = rescale_and_crop(raster_fn, mask, output_folder, res)
    outputfile = export_raster_to_geotiff(out_array, out_meta, output_folder, output_fn)

    out_array[out_array > 0] = 1
    print(
        "There are "
        + str(out_array[~np.isnan(out_array)].sum().sum())
        + " origin points."
    )

    out_fn = output_folder / "origins_points.gpkg"
    out_fn = generate_points_from_raster(outputfile, out_fn)

    return out_fn
