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


class IndirectAnalyses:
    def __init__(self, config, graph):
        self.config = config
        self.g = graph

    def single_link_redundancy(self):
        """This is the function to analyse roads with a single link disruption and an alternative route.
        :param graph: graph on which to run analysis (MultiDiGraph)
        :return: df with dijkstra detour distance and path results
        """
        logging.info("Function [single_link_redundancy]: executing.")

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
        gdf = osmnx.graph_to_gdfs(self.g, nodes=False)

        # list for the length of the alternative routes
        alt_dist_list = []
        alt_nodes_list = []
        dif_dist_list = []
        for e_remove in list(self.g.edges.data(keys=True)):
            u, v, k, data = e_remove

            # if data['highway'] in attr_list:
            # remove the edge
            self.g.remove_edge(u, v, k)

            if nx.has_path(self.g, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(self.g, u, v, weight='length')
                alt_dist_list.append(alt_dist)

                # append alternative route nodes
                alt_nodes = nx.dijkstra_path(self.g, u, v)
                alt_nodes_list.append(alt_nodes)

                # calculate the difference in distance
                dif_dist_list.append(alt_dist - data['length'])
            else:
                alt_dist_list.append(np.NaN)
                alt_nodes_list.append(np.NaN)
                dif_dist_list.append(np.NaN)

            # add edge again to the graph
            self.g.add_edge(u, v, k, **data)

        # Add the new columns to the geodataframe
        gdf['alt_dist'] = alt_dist_list
        gdf['alt_nodes'] = alt_nodes_list
        gdf['diff_dist'] = dif_dist_list

        logging.info("Full analysis [single_link_redundancy] finished.")

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return gdf

    def multi_link_redundancy(self, analysis):
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
        for hz in analysis['hazard_map']:
            attribute_name = hz.stem

            # Create a geodataframe from the full graph
            gdf = osmnx.graph_to_gdfs(self.g, nodes=False)
            gdf['unique_fid'] = gdf['unique_fid'].astype(str)

            # Create the edgelist that consist of edges that should be removed
            edges_remove = [e for e in self.g.edges.data(keys=True) if attribute_name in e[-1]]
            edges_remove = [e for e in edges_remove if
                            (e[-1][attribute_name] > float(analysis['threshold'])) & ('bridge' not in e[-1])]

            self.g.remove_edges_from(edges_remove)

            # dataframe for saving the calculations of the alternative routes
            df_calculated = pd.DataFrame(columns=['u', 'v', 'unique_fid', 'alt_dist', 'alt_nodes', 'connected'])

            for i, edges in enumerate(edges_remove):
                u, v, k, edata = edges

                # check if the nodes are still connected
                if nx.has_path(self.g, u, v):
                    # calculate the alternative distance if that edge is unavailable
                    alt_dist = nx.dijkstra_path_length(self.g, u, v, weight='length')

                    # save alternative route nodes
                    alt_nodes = nx.dijkstra_path(self.g, u, v)

                    # append to calculation dataframe
                    df_calculated = df_calculated.append(
                        {'u': u, 'v': v, 'unique_fid': str(edata['unique_fid']), 'alt_dist': alt_dist,
                         'alt_nodes': alt_nodes, 'connected': 1}, ignore_index=True)
                else:
                    # append to calculation dataframe
                    df_calculated = df_calculated.append(
                        {'u': u, 'v': v, 'unique_fid': str(edata['unique_fid']), 'alt_dist': np.NaN,
                         'alt_nodes': np.NaN, 'connected': 0}, ignore_index=True)

            # Merge the dataframes
            gdf = gdf.merge(df_calculated, how='left', on=['u', 'v', 'unique_fid'])

            # calculate the difference in distance
            gdf['diff_dist'] = [dist - length if dist == dist else np.NaN for (dist, length) in
                                zip(gdf['alt_dist'], gdf['length'])]

            gdf['hazard'] = attribute_name

            results.append(gdf)

        aggregated_results = pd.concat(results, ignore_index=True)
        return aggregated_results

    def optimal_route_origin_destination(self, analysis):
        # Calculate the preferred routes
        optimal_routes = optimal_routes_od(G, weighing, id_name, ods, crs, InputDict, shortest_route=True,
                                          save_shp=True, save_pickle=False,
                                          file_output=InputDict['output'], name=InputDict['analysis_name'])
        # dataframe to save the preferred routes
        pref_routes = gpd.GeoDataFrame(columns=['o_node', 'd_node', 'origin', 'destination',
                                                'pref_path', analysis['weighing'], 'match_ids', 'geometry'],
                                       geometry='geometry', crs='epsg:4326')

        # create list of origin-destination pairs
        self.config['output'] / od_analysis['analysis'] / (name + '_origins_destinations.p')
        od = od.replace('nan', np.nan)
        od_pairs = [(a, b) for a in od.loc[od['o_id'].notnull(), 'o_id'] for b in od.loc[od['d_id'].notnull(), 'd_id']]
        all_nodes = [(n, v['od_id']) for n, v in self.g.nodes(data=True) if 'od_id' in v]
        od_nodes = []
        for aa, bb in od_pairs:
            # it is possible that there are multiple origins/destinations at the same 'entry-point' in the road
            od_nodes.append(([(n, n_name) for n, n_name in all_nodes if (n_name == aa) | (aa in n_name)][0],
                             [(n, n_name) for n, n_name in all_nodes if (n_name == bb) | (bb in n_name)][0]))

        # create the routes between all OD pairs
        i = 0
        for o, d in tqdm(od_nodes):
            if nx.has_path(self.g, o[0], d[0]):
                # calculate the length of the preferred route
                pref_route = nx.dijkstra_path_length(self.g, o[0], d[0], weight=analysis['weighing'])

                # save preferred route nodes
                pref_nodes = nx.dijkstra_path(self.g, o[0], d[0], weight=analysis['weighing'])

                # found out which edges belong to the preferred path
                edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

                pref_edges = []
                match_list = []
                for u, v in edgesinpath:
                    # get edge with the lowest weighing if there are multiple edges that connect u and v
                    edge_key = sorted(self.g[u][v], key=lambda x: self.g[u][v][x][analysis['weighing']])[0]
                    if 'geometry' in self.g[u][v][edge_key]:
                        pref_edges.append(self.g[u][v][edge_key]['geometry'])
                    else:
                        pref_edges.append(LineString([self.g.nodes[u]['geometry'], self.g.nodes[v]['geometry']]))
                    if idName in self.g[u][v][edge_key]:
                        match_list.append(self.g[u][v][edge_key][idName])

                # compile the road segments into one geometry
                pref_edges = MultiLineString(pref_edges)
                pref_routes = pref_routes.append({'o_node': o[0], 'd_node': d[0], 'origin': o[1],
                                                  'destination': d[1], 'pref_path': pref_nodes,
                                                  analysis['weighing']: pref_route, 'match_ids': match_list,
                                                  'geometry': pref_edges}, ignore_index=True)
                i = i + 1

        # if shortest_route:
        #     pref_routes = pref_routes.loc[pref_routes.sort_values(analysis['weighing']).groupby('o_node').head(3).index]

        # intersect the origin and destination nodes with the hazard map (now only geotiff possible)
        pref_routes['d_disrupt'] = None
        pref_routes['o_disrupt'] = None
        pref_routes['d_{}'.format(hazard_data['hazard_attribute_name'][0])] = None
        pref_routes['o_{}'.format(hazard_data['hazard_attribute_name'][0])] = None
        src = rasterio.open(hazard_data['hazard_data'][0])
        for i in range(len(pref_routes.index)):
            dest = graph.nodes[int(pref_routes.d_node.iloc[i])]['geometry']
            if (src.bounds.left < dest.coords[0][0] < src.bounds.right) and (
                    src.bounds.bottom < dest.coords[0][1] < src.bounds.top):
                hzrd = [x.item(0) for x in src.sample(dest.coords)][0]
                pref_routes['d_{}'.format(hazard_data['hazard_attribute_name'][0])].iloc[i] = hzrd
                if hzrd > hazard_data['hazard_threshold']:
                    pref_routes['d_disrupt'].iloc[i] = 'disrupted'
                else:
                    pref_routes['d_disrupt'].iloc[i] = 'not disrupted'
            else:
                pref_routes['d_{}'.format(hazard_data['hazard_attribute_name'][0])].iloc[i] = 0
                pref_routes['d_disrupt'].iloc[i] = 'unknown'
            orig = graph.nodes[int(pref_routes.o_node.iloc[i])]['geometry']
            if (src.bounds.left < orig.coords[0][0] < src.bounds.right) and (
                    src.bounds.bottom < orig.coords[0][1] < src.bounds.top):
                hzrd = [x.item(0) for x in src.sample(orig.coords)][0]
                pref_routes['o_{}'.format(hazard_data['hazard_attribute_name'][0])].iloc[i] = hzrd
                if hzrd > hazard_data['hazard_threshold']:
                    pref_routes['o_disrupt'].iloc[i] = 'disrupted'
                else:
                    pref_routes['o_disrupt'].iloc[i] = 'not disrupted'
            else:
                pref_routes['o_{}'.format(hazard_data['hazard_attribute_name'][0])].iloc[i] = 0
                pref_routes['o_disrupt'].iloc[i] = 'unknown'

        return gpd.GeoDataFrame()

    def multi_link_origin_destination(self, analysis):
        return gpd.GeoDataFrame()

    def execute(self):
        """Executes the indirect analysis."""
        for analysis in self.config['indirect']:
            logging.info(f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------")
            if analysis['analysis'] == 'single_link_redundancy':
                gdf = self.single_link_redundancy()
            elif analysis['analysis'] == 'multi_link_redundancy':
                gdf = self.multi_link_redundancy(analysis)
            elif analysis['analysis'] == 'optimal_route_origin_destination':
                gdf = self.optimal_route_origin_destination(analysis)
            elif analysis['analysis'] == 'multi_link_origin_destination':
                gdf = self.multi_link_origin_destination(analysis)

            output_path = self.config['output'] / analysis['analysis']
            if analysis['save_shp'] == 'true':
                shp_path = output_path / (analysis['name'].replace(' ', '_') + '.shp')
                save_gdf(gdf, shp_path)
            if analysis['save_csv'] == 'true':
                csv_path = output_path / (analysis['name'].replace(' ', '_') + '.csv')
                del gdf['geometry']
                gdf.to_csv(csv_path, index=False)

            # Save the configuration for this analysis to the output folder.
            with open(output_path / 'settings.txt', 'w') as f:
                for key in analysis:
                    print(key + ' = ' + str(analysis[key]), file=f)
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
