# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

import logging
import networkx as nx
import osmnx
import numpy as np
from numpy import object as np_object
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
import pandas as pd
from tqdm import tqdm
import time
import copy


class IndirectAnalyses:
    def __init__(self, config):
        self.config = config

    def single_link_redundancy(self, graph, analysis):
        """This is the function to analyse roads with a single link disruption and an alternative route.
        :param graph: graph on which to run analysis (MultiDiGraph)
        :return: df with dijkstra detour distance and path results
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
        for e_remove in list(graph.edges.data(keys=True)):
            u, v, k, data = e_remove

            # if data['highway'] in attr_list:
            # remove the edge
            graph.remove_edge(u, v, k)

            if nx.has_path(graph, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(graph, u, v, weight=analysis['weighing'])
                alt_dist_list.append(alt_dist)

                # append alternative route nodes
                alt_nodes = nx.dijkstra_path(graph, u, v)
                alt_nodes_list.append(alt_nodes)

                # calculate the difference in distance
                dif_dist_list.append(alt_dist - data[analysis['weighing']])
            else:
                alt_dist_list.append(np.NaN)
                alt_nodes_list.append(np.NaN)
                dif_dist_list.append(np.NaN)

            # add edge again to the graph
            graph.add_edge(u, v, k, **data)

        # Add the new columns to the geodataframe
        gdf['alt_dist'] = alt_dist_list
        gdf['alt_nodes'] = alt_nodes_list
        gdf['diff_dist'] = dif_dist_list

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return gdf

    def multi_link_redundancy(self, graph, analysis):
        """
        The function removes all links of a variable that have a minimum value
        of min_threshold. For each link it calculates the alternative path, af
        any available. This function only removes one group at the time and saves the data from removing that group.

        Arguments:
            graph [networkx graph] = the graph with at least the columns that you use in group en sort
            attribute_name [string] = name of the attribute that indicates whether a road segment should be removed
            min_threshold [numeric] = the minimum value of the attribute by which the roads should be removed
        Returns:
            gdf [geopandas dataframe]
        """
        results = []
        for hz in self.config['hazard_names']:
            # Create a geodataframe from the full graph
            gdf = osmnx.graph_to_gdfs(graph, nodes=False)
            gdf['ra2ce_fid'] = gdf['ra2ce_fid'].astype(str)

            # Create the edgelist that consist of edges that should be removed
            edges_remove = [e for e in graph.edges.data(keys=True) if hz in e[-1]]
            edges_remove = [e for e in edges_remove if
                            (e[-1][hz] > float(analysis['threshold'])) & ('bridge' not in e[-1])]

            graph.remove_edges_from(edges_remove)

            # dataframe for saving the calculations of the alternative routes
            df_calculated = pd.DataFrame(columns=['u', 'v', 'ra2ce_fid', 'alt_dist', 'alt_nodes', 'connected'])

            for i, edges in enumerate(edges_remove):
                u, v, k, edata = edges

                # check if the nodes are still connected
                if nx.has_path(graph, u, v):
                    # calculate the alternative distance if that edge is unavailable
                    alt_dist = nx.dijkstra_path_length(graph, u, v, weight=analysis['weighing'])

                    # save alternative route nodes
                    alt_nodes = nx.dijkstra_path(graph, u, v)

                    # append to calculation dataframe
                    df_calculated = df_calculated.append(
                        {'u': u, 'v': v, 'ra2ce_fid': str(edata['ra2ce_fid']), 'alt_dist': alt_dist,
                         'alt_nodes': alt_nodes, 'connected': 1}, ignore_index=True)
                else:
                    # append to calculation dataframe
                    df_calculated = df_calculated.append(
                        {'u': u, 'v': v, 'ra2ce_fid': str(edata['ra2ce_fid']), 'alt_dist': np.NaN,
                         'alt_nodes': np.NaN, 'connected': 0}, ignore_index=True)

            # Merge the dataframes
            gdf = gdf.merge(df_calculated, how='left', on=['u', 'v', 'ra2ce_fid'])

            # calculate the difference in distance
            gdf['diff_dist'] = [dist - length if dist == dist else np.NaN for (dist, length) in
                                zip(gdf['alt_dist'], gdf[analysis['weighing']])]

            gdf['hazard'] = hz

            results.append(gdf)

        aggregated_results = pd.concat(results, ignore_index=True)
        return aggregated_results

    def optimal_route_origin_destination(self, graph, analysis):
        # Calculate the preferred routes
        name = analysis['name'].replace(' ', '_')

        # create list of origin-destination pairs
        od_path = self.config['static'] / 'output_graph' / 'origin_destination_table.feather'
        od = gpd.read_feather(od_path)
        od_pairs = [(a, b) for a in od.loc[od['o_id'].notnull(), 'o_id'] for b in od.loc[od['d_id'].notnull(), 'd_id']]
        all_nodes = [(n, v['od_id']) for n, v in graph.nodes(data=True) if 'od_id' in v]
        od_nodes = []
        for aa, bb in od_pairs:
            # it is possible that there are multiple origins/destinations at the same 'entry-point' in the road
            od_nodes.append(([(n, n_name) for n, n_name in all_nodes if (n_name == aa) | (aa in n_name)][0],
                             [(n, n_name) for n, n_name in all_nodes if (n_name == bb) | (bb in n_name)][0]))

        pref_routes = find_route_ods(graph, od_nodes, analysis['weighing'])

        # if shortest_route:
        #     pref_routes = pref_routes.loc[pref_routes.sort_values(analysis['weighing']).groupby('o_node').head(3).index]

        return pref_routes

    def multi_link_origin_destination(self, graph, analysis):
        """Calculates the connectivity between origins and destinations"""
        # create list of origin-destination pairs
        od_path = self.config['static'] / 'output_graph' / 'origin_destination_table.feather'
        od = gpd.read_feather(od_path)
        od_pairs = [(a, b) for a in od.loc[od['o_id'].notnull(), 'o_id'] for b in od.loc[od['d_id'].notnull(), 'd_id']]
        all_nodes = [(n, v['od_id']) for n, v in graph.nodes(data=True) if 'od_id' in v]
        od_nodes = []
        for aa, bb in od_pairs:
            # it is possible that there are multiple origins/destinations at the same 'entry-point' in the road
            od_nodes.append(([(n, n_name) for n, n_name in all_nodes if (n_name == aa) | (aa in n_name)][0],
                             [(n, n_name) for n, n_name in all_nodes if (n_name == bb) | (bb in n_name)][0]))

        all_results = []
        for hz in self.config['hazard_names']:
            graph_hz = copy.deepcopy(graph)

            # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
            to_remove = [(e[0], e[1], e[2]) for e in graph_hz.edges.data(keys=True) if
                         (e[-1][hz] > float(analysis['threshold'])) & ('bridge' not in e[-1])]
            # to_remove = [(e[0], e[1], e[2]) for e in graph.edges.data(keys=True) if (e[-1][hz] > float(analysis['threshold']))]
            graph_hz.remove_edges_from(to_remove)

            # Find the routes
            od_routes = find_route_ods(graph_hz, od_nodes, analysis['weighing'])
            all_results.append(od_routes)

        all_results = pd.concat(all_results, ignore_index=True)
        return all_results

    def execute(self):
        """Executes the indirect analysis."""
        for analysis in self.config['indirect']:
            logging.info(f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------")
            starttime = time.time()
            if 'weighing' in analysis:
                if analysis['weighing'] == 'distance':
                    # The name is different in the graph.
                    analysis['weighing'] = 'length'
            if analysis['analysis'] == 'single_link_redundancy':
                g = nx.read_gpickle(self.config['base_graph'])
                gdf = self.single_link_redundancy(g, analysis)
            elif analysis['analysis'] == 'multi_link_redundancy':
                g = nx.read_gpickle(self.config['base_hazard_graph'])
                gdf = self.multi_link_redundancy(g, analysis)
            elif analysis['analysis'] == 'optimal_route_origin_destination':
                g = nx.read_gpickle(self.config['origins_destinations_graph'])
                gdf = self.optimal_route_origin_destination(g, analysis)
            elif analysis['analysis'] == 'multi_link_origin_destination':
                g = nx.read_gpickle(self.config['origins_destinations_hazard_graph'])
                gdf = self.multi_link_origin_destination(g, analysis)

            output_path = self.config['output'] / analysis['analysis']
            if analysis['save_shp']:
                shp_path = output_path / (analysis['name'].replace(' ', '_') + '.shp')
                save_gdf(gdf, shp_path)
            if analysis['save_csv']:
                csv_path = output_path / (analysis['name'].replace(' ', '_') + '.csv')
                del gdf['geometry']
                gdf.to_csv(csv_path, index=False)

            # Save the configuration for this analysis to the output folder.
            with open(output_path / 'settings.txt', 'w') as f:
                for key in analysis:
                    print(key + ' = ' + str(analysis[key]), file=f)

            endtime = time.time()
            logging.info(
                f"----------------------------- Analysis '{analysis['name']}' finished. Time: {str(round(endtime - starttime, 2))}s  -----------------------------")
        return


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
    gdf.crs = 'epsg:4326'  # TODO: decide if this should be variable with e.g. an output_crs configured

    for col in gdf.columns:
        if gdf[col].dtype == np_object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(save_path, driver='ESRI Shapefile', encoding='utf-8')
    logging.info("Results saved to: {}".format(save_path))


def find_route_ods(graph, od_nodes, weighing):
    # create the routes between all OD pairs
    o_node_list, d_node_list, origin_list, destination_list, opt_path_list, weighing_list, match_ids_list, geometries_list = [], [], [], [], [], [], [], []
    for o, d in tqdm(od_nodes, desc='Finding optimal routes.'):
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
                edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing])[0]
                if 'geometry' in graph[u][v][edge_key]:
                    pref_edges.append(graph[u][v][edge_key]['geometry'])
                else:
                    pref_edges.append(LineString([graph.nodes[u]['geometry'], graph.nodes[v]['geometry']]))
                if 'ra2ce_fid' in graph[u][v][edge_key]:
                    match_list.append(graph[u][v][edge_key]['ra2ce_fid'])

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
    pref_routes = gpd.GeoDataFrame({'o_node': o_node_list, 'd_node': d_node_list, 'origin': origin_list,
                                    'destination': destination_list, 'opt_path': opt_path_list,
                                    weighing: weighing_list, 'match_ids': match_ids_list,
                                    'geometry': geometries_list}, geometry='geometry', crs='epsg:4326')
    return pref_routes
