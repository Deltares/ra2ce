import itertools
import logging
import os
import sys
import warnings
from pathlib import Path
from statistics import mean
from typing import List, Optional, Tuple, Union

import geojson
import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx
import pandas as pd
import pyproj
import rasterio
import rtree
import tqdm
import tqdm._tqdm_pandas
from geopy import distance
from networkx import Graph, set_edge_attributes
from osgeo import gdal
from osmnx.simplification import simplify_graph
from rasterio.features import shapes
from rasterio.mask import mask
from shapely.geometry import LineString, MultiLineString, Point, box, shape
from shapely.ops import linemerge, unary_union


def convert_unit(unit: str) -> Optional[float]:
    """Converts unit to meters.

    Args:
        unit (str): The unit to convert

    Returns:
        Optional[float]: The result of the conversion.
    """
    _conversion_dict = dict(centimeters=1 / 100, meters=1, feet=1 / 3.28084)
    return _conversion_dict.get(unit.lower(), None)


def drawProgressBar(percent, barLen=20):
    """Draws a progress bar
    https://stackoverflow.com/questions/3002085/python-to-print-out-status-bar-and-percentage
    """
    # percent float from 0 to 1.
    sys.stdout.write("\r")
    sys.stdout.write(
        "[{:<{}}] {:.0f}%".format("=" * int(barLen * percent), barLen, percent * 100)
    )
    sys.stdout.flush()


def merge_lines_automatic(
    lines_gdf: gpd.GeoDataFrame, idName: str, aadtNames: list, crs_: pyproj.CRS
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Automatically merge lines based on a config file
    Args:
        lines_gdf (geodataframe): the network with edges that can possibly be merged
        idName (string): name of the Unique ID column in the lines_gdf
        aadtNames (list of strings): names of the columns of the AADT (average annual daily traffic)
        crs_ (int): the EPSG number of the coordinate reference system that is used
    Returns:
        lines_gdf (geodataframe): the network with edges that are (not) merged
        lines_merged (geodataframe): the lines that are merged, if lines are merged. Otherwise it returns an empty GDF
    """
    list_lines = list(lines_gdf["geometry"])

    # Try to merge the lines
    try:
        merged_lines = linemerge(list_lines)
    except NotImplementedError as e:
        logging.error(
            "Your data contains Multi-part geometries, you cannot merge lines. Error: {}".format(
                e
            )
        )
        return lines_gdf, gpd.GeoDataFrame()
    # merge_input ='y'

    # continue
    if len(merged_lines.geoms) < len(list_lines) and aadtNames:
        # the number of merged lines is smaller than the number of lines in the input, so lines can be merged
        yes_to_all = "all"  # or in ['all', 'single']
        # ask the user if they want to take the max, min or average for all values
        all_type = "max"  # or ['max', 'min', 'mean']

    elif len(merged_lines.geoms) < len(list_lines) and not aadtNames:
        # the_input = 'y'
        lines_gdf = lines_gdf.dissolve(by=idName, aggfunc="max")
        lines_gdf.reset_index(inplace=True)

    elif len(merged_lines.geoms) == len(list_lines):
        print("No lines are merged.")
        return lines_gdf, gpd.GeoDataFrame()
    else:
        # The lines have no additional properties.
        return lines_gdf, gpd.GeoDataFrame()

    # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
    # The list of fid's is reduced by the fid's that are not anymore in the merged lines
    lines_fids = list(
        zip(list_lines, lines_gdf[idName])
    )  # create tuples from the list of lines and the list of fid's
    lines_merged = gpd.GeoDataFrame(
        columns=[idName, "geometry"], crs=crs_, geometry="geometry"
    )
    merged = gpd.GeoDataFrame(
        columns=[idName, "geometry"], crs=crs_, geometry="geometry"
    )

    for mline in merged_lines:
        for line, i in lines_fids:
            full_line = line
            if line.within(mline) and not line.equals(mline):
                # if the line is within the merged line but is not the same, the line is part of a merged line
                line_set_merged = [line]
                fid_set_merged = [i]

                if aadtNames:
                    aadts_set_merged = [
                        lines_gdf[lines_gdf[idName] == i][aadtNames].iloc[0].tolist()
                    ]
                else:
                    aadts_set_merged = []

                while not full_line.equals(mline):
                    for line2, j in lines_fids:
                        if (
                            line2.within(mline)
                            and not line2.equals(mline)
                            and line != line2
                        ):
                            line_set_merged.append(line2)
                            fid_set_merged.append(j)
                            if aadtNames:
                                aadts_set_merged.append(
                                    lines_gdf[lines_gdf[idName] == i][aadtNames]
                                    .iloc[0]
                                    .tolist()
                                )

                            lines_fids.remove(
                                (line2, j)
                            )  # remove the lines that have been through the iteration so there are no duplicates
                    full_line = linemerge(line_set_merged)
                lines_fids.remove(
                    (line, i)
                )  # remove the lines that have been through the iteration so there are no duplicates
                # the lines in this list are the same lines that make up the merged line
                add_idx = 0 if lines_merged.empty else max(lines_merged.index) + 1
                lines_merged.loc[add_idx] = {idName: i, "geometry": full_line}

                # check with the user the right traffic count for the merged lines
                if aadts_set_merged:  # check if the list is not empty
                    aadts_set_merged = [
                        i for i in aadts_set_merged if not all(v is None for v in i)
                    ]
                    if len(aadts_set_merged) > 1 and isinstance(
                        aadts_set_merged[0], list
                    ):
                        if yes_to_all == "all":
                            if all_type == "max":
                                aadts_set_merged = [
                                    max(sublist)
                                    for sublist in list(
                                        map(list, zip(*aadts_set_merged))
                                    )
                                ]
                            elif all_type == "min":
                                aadts_set_merged = [
                                    min(sublist)
                                    for sublist in list(
                                        map(list, zip(*aadts_set_merged))
                                    )
                                ]
                            elif all_type == "mean":
                                aadts_set_merged = [
                                    mean(sublist)
                                    for sublist in list(
                                        map(list, zip(*aadts_set_merged))
                                    )
                                ]

                # add values to the dataframe
                this_fid = [x[0] if isinstance(x, list) else x for x in fid_set_merged][
                    0
                ]  # take the first feature ID for the merged lines

                # initiate dict for new row in merged gdf
                properties_dict = {idName: this_fid, "geometry": mline}

                if aadtNames:
                    if isinstance(aadts_set_merged[0], list):
                        this_aadts = aadts_set_merged[0]
                    else:
                        this_aadts = aadts_set_merged

                    # update dict for new row in merged gdf
                    properties_dict.update(
                        {a: aadt_val for a, aadt_val in zip(aadtNames, this_aadts)}
                    )

                # append row to merged gdf
                add_idx = 0 if merged.empty else max(merged.index) + 1
                merged.loc[add_idx] = properties_dict

            elif line.equals(mline):
                # this line is not merged
                properties_dict = {idName: i, "geometry": mline}

                if aadtNames:
                    properties_dict.update(
                        {
                            a: aadt_val
                            for a, aadt_val in zip(
                                aadtNames,
                                lines_gdf.loc[lines_gdf[idName] == i][aadtNames].iloc[
                                    0
                                ],
                            )
                        }
                    )
                add_idx = 0 if merged.empty else max(merged.index) + 1
                merged.loc[add_idx] = properties_dict

    merged["length"] = merged["geometry"].apply(lambda x: line_length(x, crs_))

    return merged, lines_merged


def line_length(line: LineString, crs: pyproj.CRS) -> float:
    """Calculate length of a line in meters, given in geographic coordinates.
    Args:
        line: a shapely LineString object with coordinate reference system 'crs'
        crs: the coordinate reference system of the 'line' LineString
    Returns:
        Length of line in m
    """
    # Check if the coordinate system is projected or geographic
    if crs.is_geographic:
        distance.geodesic.ELLIPSOID = "WGS-84"
        try:
            # Swap shapely (lonlat) to geopy (latlon) points
            latlon = lambda lonlat: (lonlat[1], lonlat[0])
            if isinstance(line, LineString):
                total_length = sum(
                    distance.distance(latlon(a), latlon(b)).meters
                    for (a, b) in zip(line.coords, line.coords[1:])
                )
            elif isinstance(line, MultiLineString):
                total_length = sum(
                    [
                        sum(
                            distance.distance(latlon(a), latlon(b)).meters
                            for (a, b) in zip(l.coords, l.coords[1:])
                        )
                        for l in line
                    ]
                )
            else:
                logging.error(
                    "The road strech is not a Shapely LineString or MultiLineString so the length cannot be computed."
                    "Please check your data network data."
                )
                return np.nan
        except:
            logging.error(
                "The CRS is not EPSG:4326. Quit the analysis, reproject the layer to EPSG:4326 and try again to run the tool."
            )
            return np.nan
    elif crs.is_projected:
        ## line length of projected linestrings
        if isinstance(line, LineString):
            total_length = line.length
        elif isinstance(line, MultiLineString):
            total_length = line.length
        else:
            logging.error(
                "The road strech is not a Shapely LineString or MultiLineString so the length cannot be computed."
                "Please check your data network data."
            )
            return np.nan
    return round(total_length, 0)


def snap_endpoints_lines(
    lines_gdf: gpd.GeoDataFrame,
    max_dist: Union[int, float],
    idName: str,
    crs: pyproj.CRS,
) -> gpd.GeoDataFrame:
    """Snap endpoints of lines with endpoints or vertices of other lines
    if they are at most max_dist apart. Choose the closest endpoint or vertice.

    Args:
        lines_gdf: a list of LineStrings or a MultiLineString
        max_dist: maximum distance two endpoints may be joined together
        idName: the name of the ID column in lines_gdf

    From shapely_tools:
        @author: Dirk Eilander (dirk.eilander@deltares.nl)
        Adjusted 15-10-2019: Frederique de Groen (frederique.degroen@deltares.nl)
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """
    logging.info("Started snapping endpoints of lines...")
    max_id = max(lines_gdf[idName])

    # initialize snapped lines with list of original lines
    # snapping points is a MultiPoint object of all vertices
    snapped_lines = [line for line in list(lines_gdf["geometry"])]
    snapping_dict = vertices_from_lines(snapped_lines, list(lines_gdf[idName]))

    # isolated endpoints are being snapped to the closest vertex
    isolated_endpoints = find_isolated_endpoints(list(lines_gdf[idName]), snapped_lines)

    logging.info(
        "Number of isolated endpoints (points that probably need to be snapped): {} ".format(
            len(isolated_endpoints)
        )
    )
    logging.info("Snapping lines.. Follow the progress:")
    # only snap isolated endpoints within max_dist of another vertice / endpoint
    for i, isolated_endpoint in enumerate(isolated_endpoints):
        ids, endpoint = isolated_endpoint

        # create a list of the vertices that are not the line's own vertices
        points_without_linepoints = [
            value for key, value in snapping_dict.items() if key != ids
        ]

        # create list of all points to search in
        all_vertices = [p for sublist in points_without_linepoints for p in sublist]

        # create an empty spatial index object to search in
        idx = rtree.index.Index()

        # populate the spatial index
        for j, pnt in enumerate(all_vertices):
            idx.insert(j, pnt.bounds)

        # find all vertices within a radius of max_distance as possible
        # choose closest vertice and line the vertice lays on
        target = nearest_neighbor_within(all_vertices, idx, endpoint, max_dist)

        # draw a progress bar
        drawProgressBar(i / len(isolated_endpoints))

        # do nothing if the target point is further away from the endpoint than max_dist
        # or if they are at the same location
        if not target:
            continue

        # check if the line does not yet exist
        new_line = LineString([(target.x, target.y), (endpoint.x, endpoint.y)])
        if not any(new_line.equals(another_line) for another_line in snapped_lines):
            if new_line.length > 0:
                lines_gdf = lines_gdf.append(
                    {
                        idName: max_id + 1,
                        "geometry": new_line,
                        "length": line_length(new_line, crs),
                    },
                    ignore_index=True,
                )
                max_id += 1

    # TODO: remove any lines that are overlapping?

    return lines_gdf


def find_isolated_endpoints(linesIds: list, lines: list) -> list:
    """Find endpoints of lines that don't touch another line.

    Args:
        linesIds: a list of the IDs of lines
        lines: a list of LineStrings or a MultiLineString

    Returns:
        A list of line end Points that don't touch any other line of lines

    From shapely_tools:
        @author: Dirk Eilander (dirk.eilander@deltares.nl)
        Adjusted 15-10-2019: Frederique de Groen (frederique.degroen@deltares.nl)
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """
    isolated_endpoints = []
    for i, id_line in enumerate(zip(linesIds, lines)):
        ids, line = id_line
        other_lines = lines[:i] + lines[i + 1 :]
        for q in [0, -1]:
            if isinstance(line, LineString):
                endpoint = Point(line.coords[q])
                if any(endpoint.touches(another_line) for another_line in other_lines):
                    continue
                else:
                    isolated_endpoints.append((ids, endpoint))
            elif isinstance(line, MultiLineString):
                endpoints = [Point(l.coords[q]) for l in line]
                for endpnt in endpoints:
                    if any(
                        endpnt.touches(another_line) for another_line in other_lines
                    ):
                        continue
                    else:
                        isolated_endpoints.append((ids, endpnt))
    return isolated_endpoints


def nearest_neighbor_within(
    search_points: list, spatial_index, point: Point, max_distance: Union[float, int]
) -> Point:
    """Find nearest point among others up to a maximum distance.

    Args:
        search_points: list of points to search in
        spatial_index: rtree spatial index of the points to search in
        point: a Point
        max_distance: maximum distance to search for the nearest neighbor

    Returns:
        A shapely Point if one is within max_distance, None otherwise

    From shapely_tools:
        @author: Dirk Eilander (dirk.eilander@deltares.nl)
        Adjusted 15-10-2019: Frederique de Groen (frederique.degroen@deltares.nl)
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """

    # the point from where you are searching
    if isinstance(max_distance, pd.Series):
        max_distance = max_distance[0]
    geometry_buffered = point.buffer(max_distance)

    # expand bounds by max_distance in all directions
    bounds = [
        a + b * max_distance for a, b in zip(geometry_buffered.bounds, [-1, -1, 1, 1])
    ]

    # get list of fids where bounding boxes intersect
    interesting_points = [
        int(i) for i in spatial_index.intersection(geometry_buffered.bounds)
    ]

    if not interesting_points:
        closest_point = None
    elif len(interesting_points) == 1:
        closest_point = search_points[interesting_points[0]]
    else:
        points_list = [search_points[ip] for ip in interesting_points]
        distance_list = [
            (p, point.distance(p)) for p in points_list if point.distance(p) > 0
        ]
        closest_point, closest_distance = min(distance_list, key=lambda t: t[1])

    return closest_point


def vertices_from_lines(lines, listIds) -> dict:
    """Return dict of with values: unique vertices from list of LineStrings.
    keys: index of LineString in original list
    From shapely_tools:
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """
    vertices_dict = {}
    for i, line in zip(listIds, lines):
        if isinstance(line, LineString):
            vertices_dict[i] = [Point(p) for p in set(list(line.coords))]
        if isinstance(line, MultiLineString):
            all_vertices = []
            for each_line in line:
                all_vertices.extend([Point(p) for p in set(list(each_line.coords))])
            vertices_dict[i] = all_vertices
    return vertices_dict


def create_nodes(merged_lines, crs_, cut_at_intersections):
    """Creates shapely points on intersections and endpoints of a list of shapely lines
    Args:
        merged_lines [list of shapely LineStrings]: the edges of a graph
    Returns:
        nodes [list of shapely Points]: the nodes of a graph
    """
    logging.info("Started creating nodes...")
    list_lines = list(merged_lines["geometry"])

    # Get all endpoints of all linestrings
    endpts = [
        [Point(list(line.coords)[0]), Point(list(line.coords)[-1])]
        for line in list_lines
        if isinstance(line, LineString)
    ]
    # logging.info('{} Endpoints selected'.format(len(endpts)))
    # flatten the resulting list to a simple list of points
    endpts = [pt for sublist in endpts for pt in sublist]

    more_endpts = [
        [[Point(list(ln.coords)[0]), Point(list(ln.coords)[-1])] for ln in line]
        for line in list_lines
        if isinstance(line, MultiLineString)
    ]
    more_endpts = [pt for sublist in more_endpts for pt in sublist]
    more_endpts = [pt for sublist in more_endpts for pt in sublist]
    endpts.extend(more_endpts)

    if cut_at_intersections is not True:
        # create nodes on intersections and on lines that should be snapped
        inters = []
        for line1, line2 in itertools.combinations(list_lines, 2):
            # Make points at intersections of lines
            if line1.intersects(line2):
                inter = line1.intersection(line2)
                if "Point" == inter.type:
                    inters.append(inter)
                elif "MultiPoint" == inter.type:
                    inters.extend([pt for pt in inter])
                elif "MultiLineString" == inter.type:
                    multiLine = [line for line in inter]
                    first_coords = multiLine[0].coords[0]
                    last_coords = multiLine[len(multiLine) - 1].coords[1]
                    inters.append(Point(first_coords[0], first_coords[1]))
                    inters.append(Point(last_coords[0], last_coords[1]))
                elif "GeometryCollection" == inter.type:
                    for geom in inter:
                        if "Point" == geom.type:
                            inters.append(geom)
                        elif "MultiPoint" == geom.type:
                            inters.extend([pt for pt in geom])
                        elif "MultiLineString" == geom.type:
                            multiLine = [line for line in geom]
                            first_coords = multiLine[0].coords[0]
                            last_coords = multiLine[len(multiLine) - 1].coords[1]
                            inters.append(Point(first_coords[0], first_coords[1]))
                            inters.append(Point(last_coords[0], last_coords[1]))

        # Extend the endpoints with the intersection points that are not endpoints
        endpts.extend([pt for pt in inters if pt not in endpts])

    # Add to GeoDataFrame and delete duplicate points
    unique_points = delete_duplicates(endpts)
    points_gdf = gpd.GeoDataFrame(
        {"node_fid": range(len(unique_points)), "geometry": unique_points},
        geometry="geometry",
        crs=crs_,
    )

    return points_gdf


def cut_lines(lines_gdf, nodes, idName, tolerance, crs_):
    """Cuts lines at the nodes, with a certain tolerance
    Args:
        lines_gdf (geodataframe): the network with edges that should be cut
        nodes (geodataframe): points to use for cutting the edges
        idName (string): name of the Unique ID column in the lines_gdf
        tolerance: how far a point should be from the edge to cut the edge
        crs_: the CRS of the project

    Returns:
        lines_gdf (geodataframe): the network with cut edges. The IDs of the new edges counting +1 on the maximum ID number
    """
    max_id = max(lines_gdf[idName])
    list_columns = list(lines_gdf.columns.values)
    for rem in ["geometry", "length", idName]:
        list_columns.remove(rem)

    to_add = []
    to_remove = []
    to_iterate = zip(
        list(lines_gdf.index.values),
        list(lines_gdf[idName]),
        list(lines_gdf["geometry"]),
    )

    for idx, i, line in to_iterate:
        if isinstance(line, LineString):
            points_to_cut = [
                pnt
                for pnt in list(nodes["geometry"])
                if (line.distance(pnt) < tolerance)
                & (line.boundary.distance(pnt) > tolerance)
            ]
        elif isinstance(line, MultiLineString):
            points_to_cut = []
            for ln in line:
                points_to_cut.extend(
                    [
                        pnt
                        for pnt in list(nodes["geometry"])
                        if (ln.distance(pnt) < tolerance)
                        & (ln.boundary.distance(pnt) > tolerance)
                    ]
                )

        if points_to_cut:
            # cut lines
            newlines = split_line_with_points(line=line, points=points_to_cut)

            # copy and remove the row of the original linestring
            properties_dict = {}
            if list_columns:
                properties_dict = lines_gdf.loc[lines_gdf[idName] == i][
                    list_columns
                ].to_dict(orient="records")[0]

            for j, newline in enumerate(newlines):
                if j == 0:
                    # add the data with one part of the cut linestring
                    properties_dict.update(
                        {
                            idName: i,
                            "geometry": newline,
                            "length": line_length(newline, crs_),
                        }
                    )
                    logging.info(
                        "cut line segment {} {}, added new line segment with {} {}".format(
                            idName, i, idName, i
                        )
                    )
                else:
                    properties_dict.update(
                        {
                            idName: max_id + 1,
                            "geometry": newline,
                            "length": line_length(newline, crs_),
                        }
                    )
                    logging.info(
                        "cut line segment {} {}, added new line segment with {} {}".format(
                            idName, i, idName, properties_dict[idName]
                        )
                    )
                    max_id += 1

                to_add.append(properties_dict)

            # remove the original linestring that has been cut
            to_remove.append(idx)

    lines_gdf.drop(to_remove, inplace=True)
    lines_gdf = lines_gdf.append(to_add, ignore_index=True)
    return lines_gdf


def split_line_with_points(line, points):
    """Splits a line string in several segments considering a list of points."""
    segments = []
    current_line = line

    # make a list of points and its distance to the start to sort them from small to large distance
    list_dist = [current_line.project(pnt) for pnt in points]
    list_dist.sort()

    for i, d in enumerate(list_dist):
        # Subtract the previous distance from the current distance to cut the segments in the right way.
        if i > 0:
            d = d - list_dist[i - 1]

        # cut the line at a distance d
        seg, current_line = cut(current_line, d)
        if seg:
            segments.append(seg)

    segments.append(current_line)
    return segments


def cut(line, distance) -> Tuple[LineString, LineString]:
    # Cuts a line in two at a distance from its starting point
    # This is taken from shapely manual
    if (distance <= 0.0) | (distance >= line.length):
        return [None, LineString(line)]

    if isinstance(line, LineString):
        coords = list(line.coords)
        for i, p in enumerate(coords):
            pd = line.project(Point(p))
            if pd == distance:
                return [LineString(coords[: i + 1]), LineString(coords[i:])]
            if pd > distance:
                cp = line.interpolate(distance)
                # check if the LineString contains an Z-value, if so, remove
                # only use XY because otherwise the snapping functionality doesn't work
                return [
                    LineString([xy[0:2] for xy in coords[:i]] + [(cp.x, cp.y)]),
                    LineString([(cp.x, cp.y)] + [xy[0:2] for xy in coords[i:]]),
                ]
    elif isinstance(line, MultiLineString):
        for ln in line:
            coords = list(ln.coords)
            for i, p in enumerate(coords):
                pd = ln.project(Point(p))
                if pd == distance:
                    return [LineString(coords[: i + 1]), LineString(coords[i:])]
                if pd > distance:
                    cp = ln.interpolate(distance)
                    # check if the LineString contains an Z-value, if so, remove
                    # only use XY because otherwise the snapping functionality doesn't work
                    return [
                        LineString([xy[0:2] for xy in coords[:i]] + [(cp.x, cp.y)]),
                        LineString([(cp.x, cp.y)] + [xy[0:2] for xy in coords[i:]]),
                    ]


def join_nodes_edges(
    gdf_nodes: gpd.GeoDataFrame, gdf_edges: gpd.GeoDataFrame, idName: str
) -> gpd.GeoDataFrame:
    """Creates tuples from the adjecent nodes and add as column in geodataframe.
    Args:
        gdf_nodes [geodataframe]: geodataframe of the nodes of a graph
        gdf_edges [geodataframe]: geodataframe of the edges of a graph
    Returns:
        result [geodataframe]: geodataframe of adjecent nodes from edges
    """
    logging.info("Started joining edges and nodes...")
    # list of the edges that are not topographically correct
    incorrect_edges = []

    # add node attributes to edges
    gdf = gpd.sjoin(gdf_edges, gdf_nodes, how="left", op="intersects")

    tuples_df = pd.DataFrame({"node_A": [], "node_B": []})

    for edge in gdf[idName].unique():
        node_tuple = gdf.loc[gdf[idName] == edge, "node_fid"]
        if len(node_tuple) > 2:
            # if there are more than 2 nodes intersecting the linestring, choose the ones at the endpoints
            # todo: check this section carefully!!
            incorrect_edges.append(edge)
            line_nodes = gdf.loc[gdf[idName] == edge, "geometry"].iloc[0]
            if isinstance(line_nodes, LineString):
                point_coords = [
                    Point(line_nodes.coords[0]),
                    Point(line_nodes.coords[-1]),
                ]  # these are the two endpoints of the linestring - we take these as nodes
                n = gdf_nodes[
                    gdf_nodes["node_fid"].isin(node_tuple)
                ]  # get the geometries of the nodes
                special_tuple = ()
                for point in list(n.geometry):
                    if any(p.equals(point) for p in point_coords):
                        special_tuple = special_tuple + (
                            n.loc[n.geometry == point, "node_fid"].iloc[0],
                        )  # find the node id of the two endpoints of the linestring
                warnings.warn(
                    "More than two nodes are intersecting with edge {}: {}. The nodes that are intersecting are: {}".format(
                        idName, edge, list(n["node_fid"])
                    )
                )
                try:
                    tuples_df = tuples_df.append(
                        {"node_A": special_tuple[0], "node_B": special_tuple[1]},
                        ignore_index=True,
                    )
                except IndexError as e:
                    warnings.warn(
                        "Only one node can be found for edge with {} {}: {}".format(
                            idName, edge, e
                        )
                    )
            elif isinstance(line_nodes, MultiLineString):
                special_tuple = ()
                for ln in line_nodes:
                    point_coords = [
                        Point(ln.coords[0]),
                        Point(ln.coords[-1]),
                    ]  # these are the two endpoints of the linestring - we take these as nodes
                    n = gdf_nodes[
                        gdf_nodes["node_fid"].isin(node_tuple)
                    ]  # get the geometries of the nodes
                    for point in list(n.geometry):
                        if any(p.equals(point) for p in point_coords):
                            special_tuple = special_tuple + (
                                n.loc[n.geometry == point, "node_fid"].iloc[0],
                            )  # find the node id of the two endpoints of the linestring
                    logging.warning(
                        "More than two nodes are intersecting with edge {}: {}. The nodes that are intersecting are: {}".format(
                            idName, edge, list(n["node_fid"])
                        )
                    )
                try:
                    tuples_df = tuples_df.append(
                        {"node_A": special_tuple[0], "node_B": special_tuple[1]},
                        ignore_index=True,
                    )
                except IndexError as e:
                    warnings.warn(
                        "Only one node can be found for edge with {} {}: {}".format(
                            idName, edge, e
                        )
                    )
        elif len(node_tuple) < 2:
            # somehow the geopandas sjoin did not find any nodes on this edge, but there are so look for them
            node_a = [
                i
                for i, xy in zip(gdf_nodes.node_fid, gdf_nodes.geometry)
                if xy.almost_equals(
                    Point(
                        list(
                            gdf_edges.loc[gdf_edges[idName] == edge]
                            .iloc[0]
                            .geometry.coords
                        )[0]
                    )
                )
            ]
            node_b = [
                i
                for i, xy in zip(gdf_nodes.node_fid, gdf_nodes.geometry)
                if xy.almost_equals(
                    Point(
                        list(
                            gdf_edges.loc[gdf_edges[idName] == edge]
                            .iloc[0]
                            .geometry.coords
                        )[-1]
                    )
                )
            ]
            tuples_df = pd.concat(
                [
                    tuples_df,
                    pd.DataFrame.from_records(
                        [
                            {
                                "node_A": gdf_nodes.loc[
                                    gdf_nodes["node_fid"] == node_a[0], "node_fid"
                                ].iloc[0],
                                "node_B": gdf_nodes.loc[
                                    gdf_nodes["node_fid"] == node_b[0], "node_fid"
                                ].iloc[0],
                            },
                        ]
                    ),
                ],
                ignore_index=True,
            )

        elif len(node_tuple) == 2:
            # this is what you want for a good network
            tuples_df = pd.concat(
                [
                    tuples_df,
                    pd.DataFrame.from_records(
                        [
                            {
                                "node_A": node_tuple.iloc[0],
                                "node_B": node_tuple.iloc[1],
                            },
                        ]
                    ),
                ],
                ignore_index=True,
            )
        else:
            warnings.warn("Something went wrong..")

    if incorrect_edges:
        warnings.warn("More than 2 nodes intersecting edges {}".format(incorrect_edges))

    # reset indices in case they are not unique
    gdf_edges.reset_index(inplace=True, drop=True)
    tuples_df.reset_index(inplace=True, drop=True)

    result = gpd.GeoDataFrame(pd.concat([gdf_edges, tuples_df], axis=1))

    # drop all columns without values
    if result.columns[result.isnull().all()].any():
        to_drop = result.columns[result.isnull().all()]
        result.drop(to_drop, axis=1, inplace=True)

    logging.info("Function [join_nodes_edges]: executed")

    return result


def hazard_join_id_shp(roads, HazardDataDict):
    # read and join hazard data
    col_id, col_val = HazardDataDict["ID"], HazardDataDict["attribute_name"][0]

    # Fiona is not always loading the geodataframe with all data, so try a few times to get it correct
    attempts = 0
    while attempts < 3:
        try:
            hazard = gpd.read_file(HazardDataDict["path"][0])
            hazard = hazard[[col_id, col_val]]
            break
        except KeyError:
            attempts += 1
            print(
                "Attempt {} to load hazard data: {}".format(
                    attempts, HazardDataDict["path"][0].split("\\")[-1]
                )
            )

    for i in range(1, len(HazardDataDict["path"])):
        attempts = 0
        while attempts < 3:
            try:
                hazard2 = gpd.read_file(HazardDataDict["path"][i], encoding="utf-8")
                hazard = pd.concat(
                    [hazard, hazard2[[col_id, col_val]]], ignore_index=True
                )
                break
            except KeyError:
                attempts += 1
                print(
                    "Attempt {} to load hazard data: {}".format(
                        attempts, HazardDataDict["path"][i].split("\\")[-1]
                    )
                )

    if (col_val in roads) and (col_id in roads):
        hazard = pd.concat([hazard, roads[[col_id, col_val]]], ignore_index=True)

    # Not necessary now
    # hazard.drop_duplicates(inplace=True)

    for ii in hazard[col_id].unique():
        roads.loc[roads[col_id] == ii, "_{}".format(col_val)] = max(
            hazard.loc[(hazard[col_id] == ii), col_val]
        )

    return roads


def delete_duplicates(all_points: List[Point]) -> List[Point]:
    """
    Delete duplicate points given they are 'almost' equals.

    Args:
        all_points (List[Point]): List with potentially repeated points.

    Returns:
        List[Point]: List with unique points.
    """
    points = [point for point in all_points]
    uniquepoints = []
    for point in points:
        if not any(p.almost_equals(point) for p in uniquepoints):
            uniquepoints.append(point)
    return uniquepoints


def create_simplified_graph(graph_complex, new_id: str = "rfid"):
    """Create a simplified graph with unique ids from a complex graph"""
    logging.info("Simplifying graph")
    try:
        graph_complex = graph_create_unique_ids(graph_complex, "{}_c".format(new_id))

        # Create simplified graph and add unique ids
        graph_simple = simplify_graph_count(graph_complex)
        graph_simple = graph_create_unique_ids(graph_simple, new_id)

        # Create look_up_tables between graphs with unique ids
        simple_to_complex, complex_to_simple = graph_link_simple_id_to_complex(
            graph_simple, new_id=new_id
        )

        # Store id table and add simple ids to complex graph
        id_tables = (simple_to_complex, complex_to_simple)
        graph_complex = add_simple_id_to_graph_complex(
            graph_complex, complex_to_simple, new_id
        )
        logging.info("Simplified graph succesfully created")
    except:
        graph_simple = None
        id_tables = None
        logging.error("Did not create a simplified version of the graph")
    return graph_simple, graph_complex, id_tables


def gdf_check_create_unique_ids(
    gdf: gpd.GeoDataFrame, id_name: str, new_id_name: str = "rfid"
) -> Tuple[gpd.GeoDataFrame, str]:
    """
    Check if the ID's are unique per edge: if not, add an own ID called 'fid'

    Args:
        gdf (gpd.GeoDataFrame): Dataframe with edges to check.
        id_name (str): ID to search for uniqueness.
        new_id_name (str, optional): Optinal new id name to give. Defaults to "rfid".

    Returns:
        Tuple[gpd.GeoDataFrame, str]: Resulting dataframe and its ID.
    """
    check = list(gdf.index)
    logging.info("Started creating unique ids...")
    if len(gdf[id_name].unique()) == len(check):
        logging.info("Using the user-defined identifier field {}.".format(id_name))
        return gdf, id_name

    gdf[new_id_name] = check
    logging.warning(
        "Added a new unique identifier field {} because the original field '{}' "
        "did not contain unique values per road segment."
        "For further network processing, change the 'file_id' parameter in the network.ini file"
        "to '{}".format(new_id_name, id_name, new_id_name)
    )
    return gdf, new_id_name


def graph_check_create_unique_ids(
    graph: Graph, idname: str, new_id_name: str = "rfid"
) -> Tuple[Graph, str]:
    """
    TODO: This is not really being used. It could be removed.
    Check if the ID's are unique per edge: if not, add an own ID called 'fid'

    Args:
        graph (Graph): Graph to prune from repeated ids.
        idname (str): ID to search.
        new_id_name (str, optional): Optional new id to set for repeated elements. Defaults to "rfid".

    Returns:
        Tuple[Graph, str]: Resulting graph and used ID.
    """
    if len(set([str(e[-1][idname]) for e in graph.edges.data(keys=True)])) < len(
        graph.edges()
    ):

        i = 0
        for u, v, k in graph.edges(keys=True):
            graph[u][v][k][new_id_name] = i
            i += 1
        logging.info(
            "Added a new unique identifier field {} because the original field '{}' did not contain unique values per road segment.".format(
                new_id_name, idname
            )
        )
        return graph, new_id_name

    return graph, idname


def graph_create_unique_ids(graph: nx.Graph, new_id_name: str = "rfid") -> nx.Graph:
    # Check if new_id_name exists and if unique
    u, v, k = list(graph.edges)[0]
    if new_id_name in graph.edges[u, v, k]:
        return graph
    # TODO: decide if we always add a new ID (in iGraph this is different)
    # if len(set([str(e[-1][new_id_name]) for e in graph.edges.data(keys=True)])) < len(graph.edges()):
    for i, (u, v, k) in enumerate(graph.edges(keys=True)):
        graph[u][v][k][new_id_name] = i + 1
    logging.info("Added a new unique identifier field '{}'.".format(new_id_name))
    return graph


def add_missing_geoms_graph(graph: nx.Graph, geom_name: str = "geometry") -> nx.Graph:
    # Not all nodes have geometry attributed (some only x and y coordinates) so add a geometry columns
    nodes_without_geom = [
        n[0] for n in graph.nodes(data=True) if geom_name not in n[-1]
    ]
    for nd in nodes_without_geom:
        graph.nodes[nd][geom_name] = Point(graph.nodes[nd]["x"], graph.nodes[nd]["y"])

    edges_without_geom = [
        e for e in graph.edges.data(keys=True) if geom_name not in e[-1]
    ]
    for ed in edges_without_geom:
        graph[ed[0]][ed[1]][ed[2]][geom_name] = LineString(
            [graph.nodes[ed[0]][geom_name], graph.nodes[ed[1]][geom_name]]
        )

    return graph


def simplify_graph_count(G_complex: nx.Graph) -> nx.Graph:
    # Simplify the graph topology and log the change in nr of nodes and edges.
    old_len_nodes = G_complex.number_of_nodes()
    old_len_edges = G_complex.number_of_edges()

    G_simple = simplify_graph(G_complex)

    new_len_nodes = G_simple.number_of_nodes()
    new_len_edges = G_simple.number_of_edges()

    logging.info(
        "Graph simplified from {:,} to {:,} nodes and {:,} to {:,} edges.".format(
            old_len_nodes, new_len_nodes, old_len_edges, new_len_edges
        )
    )

    return G_simple


def read_geojson(geojson_file: Path) -> dict:
    """Read a GeoJSON file into a GeoJSON object.
    From the script get_rcm.py from Martijn Kwant.
    """
    with open(geojson_file) as f:
        return geojson.load(f)


def graph_from_gdf(
    gdf: gpd.GeoDataFrame, gdf_nodes, name: str = "network", node_id: str = "ID"
) -> nx.MultiGraph:
    # create a Graph object
    G = nx.MultiGraph(crs=gdf.crs)

    # create nodes on the Graph
    for index, row in gdf_nodes.iterrows():
        c = {node_id: row[node_id], "geometry": row.geometry}
        G.add_node(row[node_id], **c)

    # create edges on top of the nodes
    for index, row in gdf.iterrows():
        dict_row = row.to_dict()
        G.add_edge(
            u_for_edge=dict_row["node_A"], v_for_edge=dict_row["node_B"], **dict_row
        )

    # make a name
    G.graph["name"] = name

    return G


def graph_to_gdf(
    G: nx.classes.graph.Graph, save_nodes=False, save_edges=True, to_save=False
):
    """Takes in a networkx graph object and returns edges and nodes as geodataframes
    Arguments:
        G (Graph): networkx graph object to be converted

    Returns:
        edges (GeoDataFrame) : containes the edges
        nodes (GeoDataFrame) :
    """

    nodes, edges = None, None
    if save_nodes and save_edges:
        nodes, edges = osmnx.graph_to_gdfs(
            G, nodes=save_nodes, edges=save_edges, node_geometry=False
        )

        if to_save:
            dfs = [edges, nodes]
            for df in dfs:
                for col in df.columns:
                    if df[col].dtype == object and col != df.geometry.name:
                        df[col] = df[col].astype(str)

    elif not save_nodes and save_edges:
        edges = osmnx.graph_to_gdfs(G, nodes=save_nodes, edges=save_edges)
    elif save_nodes and not save_edges:
        nodes = osmnx.graph_to_gdfs(G, nodes=save_nodes, edges=save_edges)

    return edges, nodes


def graph_to_gpkg(G, edge_gpkg, node_gpkg):
    """Takes in a networkx graph object and outputs shapefiles at the paths indicated by edge_gpkg and node_gpkg

    Arguments:
        G []: networkx graph object to be converted
        edge_gpkg [str]: output path including extension for edges geopackage
        node_gpkg [str]: output path including extension for nodes geopackage

    Returns:
        None

    """
    # now only multidigraphs and graphs are used
    if type(G) == nx.classes.graph.Graph:
        G = nx.MultiGraph(G)

    # The nodes should have a geometry attribute (perhaps on top of the x and y attributes)
    nodes, edges = osmnx.graph_to_gdfs(G, node_geometry=False)

    dfs = [edges, nodes]
    for df in dfs:
        for col in df.columns:
            if df[col].dtype == object and col != df.geometry.name:
                df[col] = df[col].astype(str)

    # Add a CRS to the nodes
    if nodes.crs is None and edges.crs is not None:
        nodes.crs = edges.crs

    logging.info("Saving nodes as shapefile: {}".format(node_gpkg))
    logging.info("Saving edges as shapefile: {}".format(edge_gpkg))

    # The encoding utf-8 might result in an empty shapefile if the wrong encoding is used.
    nodes.to_file(node_gpkg, driver="GPKG", encoding="utf-8")
    edges.to_file(edge_gpkg, driver="GPKG", encoding="utf-8")


def geojson_to_shp(geojson_obj, feature_number=0):
    """Convert a GeoJSON object to a Shapely Polygon.
    Adjusted from the script get_rcm.py from Martijn Kwant.

    In case of FeatureCollection, only one of the features is used (the first by default).
    3D points are converted to 2D.

    Parameters
    ----------
    geojson_obj : dict
        a GeoJSON object
    feature_number : int, optional
        Feature to extract polygon from (in case of MultiPolygon
        FeatureCollection), defaults to first Feature

    Returns
    -------
    polygon coordinates
        string of comma separated coordinate tuples (lon, lat) to be used by SentinelAPI
    """
    if "coordinates" in geojson_obj:
        geometry = geojson_obj
    elif "geometry" in geojson_obj:
        geometry = geojson_obj["geometry"]
    else:
        geometry = geojson_obj["features"][feature_number]["geometry"]

    def ensure_2d(geometry):
        if isinstance(geometry[0], (list, tuple)):
            return list(map(ensure_2d, geometry))
        else:
            return geometry[:2]

    def check_bounds(geometry):
        if isinstance(geometry[0], (list, tuple)):
            return list(map(check_bounds, geometry))
        else:
            if geometry[0] > 180 or geometry[0] < -180:
                raise ValueError(
                    "Longitude is out of bounds, check your JSON format or data. The Coordinate Reference System should be in EPSG:4326."
                )
            if geometry[1] > 90 or geometry[1] < -90:
                raise ValueError(
                    "Latitude is out of bounds, check your JSON format or data. The Coordinate Reference System should be in EPSG:4326."
                )

    # Discard z-coordinate, if it exists
    geometry["coordinates"] = ensure_2d(geometry["coordinates"])
    check_bounds(geometry["coordinates"])

    # Create a shapely polygon from the coordinates.
    poly = shape(geometry).buffer(0)
    return poly


def read_merge_shp(shapefileAnalyse, idName, shapefileDiversion=[], crs_=4326):
    """Imports shapefile(s) and saves attributes in a pandas dataframe.

    Args:
        shapefileAnalyse (string or list of strings): absolute path(s) to the shapefile(s) that will be used for analysis
        shapefileDiversion (string or list of strings): absolute path(s) to the shapefile(s) that will be used to calculate alternative routes but is not analysed
        idName (string): the name of the Unique ID column
        crs_ (int): the EPSG number of the coordinate reference system that is used
    Returns:
        lines (list of shapely LineStrings): full list of linestrings
        properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
    """

    # convert shapefile names to a list if it was not already a list
    if isinstance(shapefileAnalyse, str):
        shapefileAnalyse = [shapefileAnalyse]
    if isinstance(shapefileDiversion, str):
        shapefileDiversion = [shapefileDiversion]

    lines = []

    # read the shapefile(s) for analysis
    for shp in shapefileAnalyse:
        lines_shp = gpd.read_file(shp)
        lines_shp["to_analyse"] = 1
        lines.append(lines_shp)

    # read the shapefile(s) for only diversion
    if isinstance(shapefileDiversion, list):
        for shp2 in shapefileDiversion:
            lines_shp = gpd.read_file(shp2)
            lines_shp["to_analyse"] = 0
            lines.append(lines_shp)

    # concatenate all shapefiles into one geodataframe
    lines = pd.concat(lines)
    lines.crs = crs_

    # append the length of the road stretches
    lines["length"] = lines["geometry"].apply(lambda x: line_length(x, crs_))

    if lines["geometry"].apply(lambda row: isinstance(row, MultiLineString)).any():
        for line in lines.loc[
            lines["geometry"].apply(lambda row: isinstance(row, MultiLineString))
        ].iterrows():
            if len(linemerge(line[1].geometry)) > 1:
                warnings.warn(
                    "Edge with {} = {} is a MultiLineString, which cannot be merged to one line. Check this part.".format(
                        idName, line[1][idName]
                    )
                )

    print(
        "Shapefile(s) loaded with attributes: {}.".format(list(lines.columns.values))
    )  # fill in parameter names

    return lines


def check_hazard_extent_resolution(list_hazards):
    """Checks whether the extent of a list of hazard rasters is exactly the same.

    Args:
        list_hazards (list of pathlib paths or strings): A list of paths to the hazard map rasters of which
            the extent needs to be checked

    Returns:
        (bool): True if the extents are exactly the same, False if they are not.
    """
    if len(list_hazards) == 1:
        return True
    check_hazard_extent = [
        gdal.Open(str(haz)).GetGeoTransform() for haz in list_hazards
    ]
    if len(set(check_hazard_extent)) == 1:
        # All hazard have the exact same extents and resolution
        return True
    else:
        return False


def get_extent(dataset):
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    transform = dataset.GetGeoTransform()
    minx = transform[0]
    maxx = transform[0] + cols * transform[1] + rows * transform[2]

    miny = transform[3] + cols * transform[4] + rows * transform[5]
    maxy = transform[3]

    width = maxx - minx
    height = maxy - miny

    return {
        "minX": minx,
        "maxX": maxx,
        "minY": miny,
        "maxY": maxy,
        "cols": cols,
        "rows": rows,
        "width": width,
        "height": height,
        "pixelWidth": transform[1],
        "pixelHeight": transform[5],
    }


def get_graph_edges_extent(G):
    """Inspects all geometries of the edges of a graph and returns the most extreme coordinates

    Arguments:
        G (networkX) : NetworkX graph, should have an attribute 'geometry' containty shapely geometries

    Returns
        extent (tuple) : (minX,maxX,minY,maxY)
    """
    # Start with the bounds of the (random) first edge
    (minX, minY, maxX, maxY) = list(G.edges.data("geometry"))[0][-1].bounds

    # Compare with the bounds of all other edges to see if there are linestrings with more extreme bounds
    for (u, v, geom) in G.edges.data("geometry"):
        # print(u, v, geom)
        (
            minx,
            miny,
            maxx,
            maxy,
        ) = geom.bounds  # shapely returns (minx, miny, maxx, maxy)
        if minx < minX:
            minX = minx
        if maxx > maxX:
            maxX = maxx
        if miny < minY:
            minY = miny
        if maxy > maxY:
            maxY = maxy

    return (minX, maxX, minY, maxY)


def reproject_graph(G_in, crs_in, crs_out):
    """
    Reprojects the shapely geometry data (of a NetworkX graph) to a different projection

    Arguments:
        G_in (NetworkX graph): needs a geometry attribute containing shapely linestrings
        crs_in (string): input projection, follow the Geopandas crs convention: "espg:3035" or "EPSG4326"
        crs_out (string): output projection to covert to, idem.

    Returns:
        G_out (NetworkX graph)
    """
    att = nx.get_edge_attributes(G_in, "geometry")
    df = pd.DataFrame.from_dict(data=att, orient="index", columns=["geometry"])
    gdf = gpd.GeoDataFrame(df)
    gdf = gdf.set_crs(crs=crs_in)
    gdf_out = gdf.to_crs(crs=crs_out)
    G_out = G_in.copy()
    set_values = gdf_out.to_dict(orient="index")
    nx.set_edge_attributes(G_out, values=set_values)
    return G_out


def bounds_intersect_1d(tup1, tup2):
    """Check if bounds of A and B intersect anywhere (have any overlapping points)

    Arguments:
        tup1 (tuple) : (min, max)
        tup2 (tuple) : (min, max)

    Returns:
        Boolean (True/False)
    """
    return (tup1[0] <= tup2[1]) and (tup1[1] >= tup2[0])


def bounds_intersect_2d(extent1, extent2):
    """
    check if bounds of A and B intersect anywhere (have any overlapping area)

    Arguments:
        *extent1* (tuple) : (minx,maxx,miny,maxy)
        *extent2* (tuple) : (minx,maxx,miny,maxy)

    Returns:
        Boolean (True/False)
    """
    x_overlap = bounds_intersect_1d((extent1[0], extent1[1]), (extent2[0], extent2[1]))
    y_overlap = bounds_intersect_1d((extent1[2], extent1[3]), (extent2[2], extent2[3]))
    return x_overlap and y_overlap


def convert_osm(osm_convert_path, pbf, o5m):
    """Converse an osm PBF file to o5m"""
    command = '""{}"  "{}" --complete-ways --drop-broken-refs -o="{}""'.format(
        osm_convert_path, pbf, o5m
    )
    os.system(command)


def filter_osm(osm_filter_path, o5m, filtered_o5m, tags=None):
    """Filters an o5m OSM file to only motorways, trunks, primary and secondary roads (or tags, if specified)"""
    if tags is None:
        tags = [
            "motorway",
            "motorway_link",
            "primary",
            "primary_link",
            "secondary",
            "secondary_link",
            "trunk",
            "trunk_link",
        ]
    command = '""{}"  "{}" --keep="highway={}" > "{}""'.format(
        osm_filter_path, o5m, " =".join(tags), filtered_o5m
    )
    os.system(command)


def graph_link_simple_id_to_complex(graph_simple, new_id):
    """
    Create lookup tables (dicts) to match edges_ids of the complex and simple graph
    Optionally, saves these lookup tables as json files.

    Arguments:
        graph_simple (Graph) : Graph, containing attribute 'new_id'
        new_id (string) : Name of the ID attribute in graph_simple

    Returns:
        simple_to_complex (dict): Keys are ids of the simple graph, values are lists with all matching complex ids
        complex_to_simple (dict): Keys are the ids of the complex graph, value is the matching simple_ID

    We need this because the simple graph is derived from the complex graph, and therefore initially only the
    simple graph knows from which complex edges it was created. To assign this information also to the complex
    graph we invert the look-up dictionary
    @author: Kees van Ginkel en Margreet van Marle
    """
    # Iterate over the simple, because this already has the corresponding complex information
    lookup_dict = {}
    # keys are the ids of the simple graph, values are lists with all matching complex id's
    for u, v, k in tqdm.tqdm(graph_simple.edges(keys=True)):
        key_1 = graph_simple[u][v][k]["{}".format(new_id)]
        value_1 = graph_simple[u][v][k]["{}_c".format(new_id)]
        lookup_dict[key_1] = value_1

    inverted_lookup_dict = {}
    # keys are the ids of the complex graph, value is the matching simple_ID
    for key, value in lookup_dict.items():
        if isinstance(value, list):
            for subvalue in value:
                inverted_lookup_dict[subvalue] = key
        elif isinstance(value, int):
            inverted_lookup_dict[value] = key

    simple_to_complex = lookup_dict
    complex_to_simple = inverted_lookup_dict

    logging.info("Lookup tables from complex to simple and vice versa were created")
    return simple_to_complex, complex_to_simple


def add_simple_id_to_graph_complex(G_complex, complex_to_simple, new_id):
    """Adds the appropriate ID of the simple graph to each edge of the complex graph as a new attribute 'rfid'

    Arguments:
        G_complex (Graph) : The complex graph, still lacking 'rfid'
        complex_to_simple (dict) : lookup table linking complex to simple graphs

    Returns:
         G_complex (Graph) : Same object, with added attribute 'rfid'

    """

    obtained_complex_ids = nx.get_edge_attributes(
        G_complex, "{}_c".format(new_id)
    )  # {(u,v,k) : 'rfid_c'}
    simple_ids_per_complex_id = obtained_complex_ids  # start with a copy

    for key, value in obtained_complex_ids.items():  # {(u,v,k) : 'rfid_c'}
        try:
            new_value = complex_to_simple[
                value
            ]  # find simple id belonging to the complex id
            simple_ids_per_complex_id[key] = new_value
        except KeyError as e:
            logging.error(
                "Could not find the simple ID belonging to complex ID {}; value set to None".format(
                    key
                )
            )
            simple_ids_per_complex_id[key] = None

    # Now the format of simple_ids_per_complex_id is: {(u,v,k) : 'rfid}
    set_edge_attributes(G_complex, simple_ids_per_complex_id, new_id)

    return G_complex


def calc_avg_speed(graph, road_type_col_name, save_csv=False, save_path=None):
    """Calculates the average speed from OSM roads, per road type

    Args:
        graph (NetworkX graph): NetworkX graph with road types
        road_type_col_name (string): name of the column which holds the road types ('highway' in OSM)
        save_csv (boolean): To save a csv or not
        save_path (string): Path to save the csv to

    Returns:
        df (Pandas DataFrame): Dataframe with the average road speeds per road type
    """
    # Create a dataframe of all road types
    exceptions = list(
        set(
            [
                str(edata[road_type_col_name])
                for u, v, edata in graph.edges.data()
                if isinstance(edata[road_type_col_name], list)
            ]
        )
    )
    types = list(
        set(
            [
                str(edata[road_type_col_name])
                for u, v, edata in graph.edges.data()
                if isinstance(edata[road_type_col_name], str)
            ]
        )
    )
    all_road_types = exceptions + types
    df = pd.DataFrame({"road_types": all_road_types, "avg_speed": 0})

    # calculate average speed
    for i in range(len(df)):
        roadtype = df.road_types[i]
        all_edges = [
            (u, v, edata["maxspeed"], edata["length"])
            for u, v, edata in graph.edges.data()
            if (str(edata[road_type_col_name]) == roadtype) & ("maxspeed" in edata)
        ]
        all_avg = []
        all_l = []
        for u, v, s, l in all_edges:
            if isinstance(s, list):
                ns = []
                for ss in s:
                    if (
                        not any(c.isalpha() for c in ss)
                        and not (";" in ss)
                        and not ("|" in ss)
                    ):
                        ns.append(int(ss))
                    elif not any(c.isalpha() for c in ss) and ";" in ss:
                        ns.extend([int(x) for x in ss.split(";") if x.isnumeric()])
                    elif not any(c.isalpha() for c in ss) and "|" in ss:
                        ns.extend([int(x) for x in ss.split("|") if x.isnumeric()])
                    elif " mph" in ss:
                        ns.append(int(ss.split(" mph")[0]) * 1.609344)
                if len(ns) > 0:
                    ss = sum(ns) / len(ns)
                else:
                    continue
            elif isinstance(s, str):
                if (
                    not any(c.isalpha() for c in s)
                    and not (";" in s)
                    and not ("|" in s)
                ):
                    ss = int(s)
                elif not any(c.isalpha() for c in s) and ";" in s:
                    ss = mean([int(x) for x in s.split(";") if x.isnumeric()])
                elif not any(c.isalpha() for c in s) and "|" in s:
                    ss = mean([int(x) for x in s.split("|") if x.isnumeric()])
                elif " mph" in s:
                    ss = int(s.split(" mph")[0]) * 1.609344
                else:
                    continue
            all_avg.append(ss * l)
            all_l.append(l)
            df.iloc[i, 1] = sum(all_avg) / sum(all_l)

    # For all types without an average speed, take one that is closest. E.g. for the links take the one of the same type
    # of the main roads
    if not df.loc[df["avg_speed"] == 0].empty:
        logging.info(
            f"Not all of the edges contain a 'maxspeed' attribute. RA2CE will guess the right average maximum "
            f"speed per road type that does not contain a 'maxspeed' attribute. Please check the average speed CSV to ensure correct speeds here: {save_path}"
        )
        for i in df.loc[df["avg_speed"] == 0].index:
            if df["road_types"].iloc[i] in exceptions:
                if any(rt in df["road_types"].iloc[i] for rt in df["road_types"]):
                    road_type, avg_speed = [
                        (rt, avg_s)
                        for rt, avg_s in zip(df["road_types"], df["avg_speed"])
                        if rt in df["road_types"].iloc[i] and avg_s != 0
                    ][0]
                    df["avg_speed"].iloc[i] = avg_speed
            else:
                # if any(rt in df['road_types'].iloc[i] for rt in df['road_types']):
                if "link" in df["road_types"].iloc[i]:
                    try:
                        df["avg_speed"].iloc[i] = df.loc[
                            df["road_types"]
                            == df["road_types"].iloc[i].split("_link")[0],
                            "avg_speed",
                        ].values[0]
                    except IndexError as e:
                        logging.warning(
                            f"Road type '{df['road_types'].iloc[i]}' cannot be assigned any average speed. Please check the average speed CSV ({save_path}), enter the right average speed for this road type, and run RA2CE again."
                        )
                        df["avg_speed"].iloc[i] = 0

    if save_csv:
        df.to_csv(save_path)
        logging.info("Saved the average speeds per road type to: {}".format(save_path))

    return df


def assign_avg_speed(graph, avg_road_speed, road_type_col_name):
    """Assigns the average speed to roads in an existing (OSM) graph

    Args:
        graph (NetworkX graph): NetworkX graph with road types
        avg_road_speed (Pandas DataFrame): a Dataframe with columns "road_types" and "maxspeed"
        road_type_col_name (string): Attribute name of the road type in the NetworkX graph

    Returns:
        graph (NetworkX graph): NetworkX graph with an additional attribute 'avgspeed'
    """
    # make a list of strings instead of just a string of the road types column
    avg_road_speed["road_types"] = avg_road_speed["road_types"].astype(str)

    # calculate the average maximum speed per edge and assign the ones that don't have a value
    for u, v, k, edata in graph.edges.data(keys=True):
        road_type = str(edata[road_type_col_name])
        if "maxspeed" in edata:
            max_speed = edata["maxspeed"]
            if isinstance(max_speed, list):
                ns = []
                for ms in max_speed:
                    if (
                        not any(c.isalpha() for c in ms)
                        and not (";" in ms)
                        and not ("|" in ms)
                    ):
                        ns.append(int(ms))
                    elif not any(c.isalpha() for c in ms) and ";" in ms:
                        ns.extend([int(x) for x in ms.split(";") if x.isnumeric()])
                    elif not any(c.isalpha() for c in ms) and "|" in ms:
                        ns.extend([int(x) for x in ms.split("|") if x.isnumeric()])
                    elif " mph" in ms:
                        ns.append(int(ms.split(" mph")[0]) * 1.609344)
                if len(ns) > 0:
                    graph[u][v][k]["avgspeed"] = round(sum(ns) / len(ns), 0)
                else:
                    graph[u][v][k]["avgspeed"] = round(
                        avg_road_speed.loc[
                            avg_road_speed["road_types"] == road_type, "avg_speed"
                        ].iloc[0],
                        0,
                    )
            elif isinstance(max_speed, str):
                if (
                    not any(c.isalpha() for c in max_speed)
                    and not (";" in max_speed)
                    and not ("|" in max_speed)
                ):
                    graph[u][v][k]["avgspeed"] = round(int(max_speed), 0)
                elif not any(c.isalpha() for c in max_speed) and ";" in max_speed:
                    graph[u][v][k]["avgspeed"] = round(
                        mean([int(x) for x in max_speed.split(";") if x.isnumeric()]), 0
                    )
                elif not any(c.isalpha() for c in max_speed) and "|" in max_speed:
                    graph[u][v][k]["avgspeed"] = round(
                        mean([int(x) for x in max_speed.split("|") if x.isnumeric()]), 0
                    )
                elif " mph" in max_speed:
                    graph[u][v][k]["avgspeed"] = round(
                        int(max_speed.split(" mph")[0]) * 1.609344, 0
                    )
                else:
                    graph[u][v][k]["avgspeed"] = round(
                        avg_road_speed.loc[
                            avg_road_speed["road_types"] == road_type, "avg_speed"
                        ].iloc[0],
                        0,
                    )
        else:
            if "]" in road_type:
                avg_speed = int(
                    [
                        s
                        for r, s in zip(
                            avg_road_speed["road_types"], avg_road_speed["avg_speed"]
                        )
                        if set(road_type[2:-2].split("', '"))
                        == set(r[2:-2].split("', '"))
                    ][0]
                )
                graph[u][v][k]["avgspeed"] = round(avg_speed, 0)
            else:
                graph[u][v][k]["avgspeed"] = round(
                    avg_road_speed.loc[
                        avg_road_speed["road_types"] == road_type, "avg_speed"
                    ].iloc[0],
                    0,
                )

    return graph


def fraction_flooded(line: LineString, hazard_map: str):
    """Calculates the fraction of a linestring that overlaps with a hazard raster with value > 0

    Args:
        line (LineString): A single linestring that should be overlayed with the hazard map.
        hazard_map (string): Full path to the hazard map.

    Returns:
        (float) The fraction of the linestring that overlaps with the hazard raster with a value > 0.
        (0) If there is a ValueError, for example, if the linestring has no overlap with the raster,
        the function returns 0.
    """

    bbox_line = box(*line.bounds)
    try:
        with rasterio.open(hazard_map) as src:
            out_image, out_transform = mask(
                src, [bbox_line], crop=True, all_touched=True
            )

        flooded_cells = unary_union(
            [
                shape(x[0])
                for x in shapes(out_image, transform=out_transform)
                if x[-1] > 0
            ]
        )
        flooded_cells = gpd.GeoDataFrame({"geometry": [flooded_cells]})

        line_intersect = flooded_cells.intersection(line)
        return line_intersect.length.sum() / line.length
    except ValueError:
        return 0
    except Exception as e:
        logging.info("fraction_flooded() {} \n for line {}".format(e, line))


def check_crs_gdf(gdf: gpd.GeoDataFrame, crs) -> None:
    if gdf.crs != crs:
        logging.error(
            "Shape projection is epsg:{} - only projection epsg:{} is allowed. ".format(
                gdf.crs, crs
            )
        )
        sys.exit()


def clean_memory(list_delete: list) -> None:
    for to_delete in list_delete:
        del to_delete


def get_valid_mean(x_value: float) -> Optional[float]:
    if not isinstance(x_value, float):
        return np.nan
    return x_value.mean()  # You know it's a valid type, so return the mean.
