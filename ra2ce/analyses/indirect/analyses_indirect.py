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
    def __init__(self, config, graphs):
        self.config = config
        self.graphs = graphs

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
            edges_remove = [e for e in graph.edges.data(keys=True) if hz+'_'+analysis['aggregate_wl'] in e[-1]]
            edges_remove = [e for e in edges_remove if
                            (e[-1][hz+'_'+analysis['aggregate_wl']] > float(analysis['threshold'])) & ('bridge' not in e[-1])]

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

            gdf['hazard'] = hz+'_'+analysis['aggregate_wl']

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
                         (e[-1][hz+'_'+analysis['aggregate_wl']] > float(analysis['threshold'])) & ('bridge' not in e[-1])]
            # to_remove = [(e[0], e[1], e[2]) for e in graph.edges.data(keys=True) if (e[-1][hz+'_'+analysis['aggregate_wl']] > float(analysis['threshold']))]
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
                g = nx.read_gpickle(self.config['files']['base_graph'])
                gdf = self.single_link_redundancy(g, analysis)
            elif analysis['analysis'] == 'multi_link_redundancy':
                g = nx.read_gpickle(self.config['files']['base_graph_hazard'])
                gdf = self.multi_link_redundancy(g, analysis)
            elif analysis['analysis'] == 'optimal_route_origin_destination':
                g = nx.read_gpickle(self.config['files']['origins_destinations_graph'])
                gdf = self.optimal_route_origin_destination(g, analysis)
            elif analysis['analysis'] == 'multi_link_origin_destination':
                g = nx.read_gpickle(self.config['files']['origins_destinations_graph_hazard'])
                gdf = self.multi_link_origin_destination(g, analysis)
            elif analysis['analysis'] == 'losses':

                if self.graphs['base_network_hazard'] is None:
                    gdf_in = gpd.read_feather(self.config['files']['base_network_hazard'])

                losses = Losses(self.config, analysis)
                df = losses.calculate_losses_from_table()
                gdf = gdf_in.merge(df, how='left', on='LinkNr')

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


class Losses:
    def __init__(self, config, analysis):
        self.config = config
        self.analysis = analysis
        self.duration = analysis['duration_event']
        self.duration_disr = analysis['duration_disruption']
        self.detour_traffic = analysis['fraction_detour']
        self.traffic_throughput = analysis['fraction_drivethrough']
        self.rest_capacity = analysis['rest_capacity']
        self.maximum = analysis['maximum_jam']
        self.partofday = analysis['partofday']

    @staticmethod
    def vehicle_loss_hours(path):
        """ This function is to calculate vehicle loss hours based on an input table
        with value of time per type of transport, usage and value_of_reliability """

        file_path = path / 'vehicle_loss_hours.csv'
        df_lookup = pd.read_csv(file_path, index_col='transport_type')
        lookup_dict = df_lookup.transpose().to_dict()

        # detour_data = pd.read_csv(path / 'detour_data_header.csv', names=['file', 'replace']).set_index('file')
        # detour_dict = detour_data.to_dict()['replace']
        # detour_data = pd.read_csv(path / 'traffic_intensities_header.csv', names=['file', 'replace']).set_index('file')
        # dict2 = detour_data.to_dict()['replace']
        # detour_data = pd.read_csv(path / 'vehicle_loss_hours_header.csv', names=['file', 'replace']).set_index('file')
        # dict3 = detour_data.to_dict()['replace']
        #
        # dict1 = {'VA_AV_HWN': 'detour_time_evening', 'VA_RD_HWN': 'detour_time_remaining', 'VA_OS_HWN': 'detour_time_morning', 'VA_Etm_HWN': 'detour_time_day'}
        # dict2 ={'AS_VTG': 'evening_total', 'AS_FRGT': 'evening_freight', 'AS_COMM': 'evening_commute', 'AS_BUSS': 'evening_business', 'AS_OTHR': 'evening_other', 'ET_FRGT': 'day_freight', 'ET_COMM': 'day_commute', 'ET_BUSS': 'day_business', 'ET_OTHR': 'day_other', 'ET_VTG': 'day_total', 'afstand': 'distance', 'H_Cap': 'capacity', 'H_Stroken': 'lanes'}
        # dict3 ={'VOT_hour': 'value_of_time',
        #         'Occupation': 'occupation',
        #         'VoR': 'value_of_reliability',
        #         'VVU (€/uur)': 'vehicle_loss_hour',
        #         'Type of transport': 'transport_type',
        #         'Vracht (FRG)': 'freight',
        #         'Forens (COMM)': 'commute',
        #         'Zakelijk (BUSS)': 'bussiness',
        #         'Overig (OTHER)': 'other'}

        return lookup_dict

    @staticmethod
    def load_df(path, file):
        """ This method reads the dataframe created from a .csv """
        file_path = path / file
        df = pd.read_csv(file_path, index_col='LinkNr')
        return df

    def traffic_shockwave(self, vlh, capacity, intensity):
        vlh['vlh_traffic'] = (self.duration ** 2) * (self.rest_capacity - 1) * (self.rest_capacity * capacity - intensity / self.traffic_throughput) / (2 * (1 - ((intensity / self.traffic_throughput) / capacity)))
        return vlh

    def calc_vlh(self, traffic_data, vehicle_loss_hours, detour_data):
        vlh = pd.DataFrame(index=traffic_data.index, columns=['vlh_traffic', 'vlh_detour', 'vlh_total', 'euro_per_hour', 'euro_vlh'])
        capacity = traffic_data['capacity']
        diff_event_disr = self.duration - self.duration_disr

        if self.partofday == 'daily':
            intensity = traffic_data['day_total'] / 24
            detour_time = detour_data['detour_time_day']
        if self.partofday == 'evening':
            intensity = traffic_data['evening_total']
            detour_time = detour_data['detour_time_evening']

        vlh = self.traffic_shockwave(vlh, capacity, intensity)
        vlh['vlh_traffic'] = vlh['vlh_traffic'].apply(lambda x: np.where(x < 0, 0, x))  # all values below 0 -> 0
        vlh['vlh_traffic'] = vlh['vlh_traffic'].apply(lambda x: np.where(x > self.maximum, self.maximum, x))
        # all values above maximum, limit to maximum
        vlh['vlh_detour'] = (intensity * ((1 - self.traffic_throughput) * self.duration) * detour_time) / 60
        vlh['vlh_detour'] = vlh['vlh_detour'].apply(lambda x: np.where(x < 0, 0, x))  # all values below 0 -> 0
        
        if diff_event_disr > 0:  # when the event is done, but the disruption continues after the event. Calculate extra detour times
            temp = diff_event_disr * (detour_time * self.detour_traffic * detour_time) / 60
            temp = temp.apply(lambda x: np.where(x < 0, 0, x))  # all values below 0 -> 0
            vlh['vlh_detour'] = vlh['vlh_detour'] + temp

        vlh['vlh_total'] = vlh['vlh_traffic'] + vlh['vlh_detour']

        if self.partofday == 'daily':
            vlh['euro_per_hour'] =(traffic_data['day_freight']/traffic_data['day_total']*vehicle_loss_hours['freight']['vehicle_loss_hour'])+\
                                (traffic_data['day_commute']/traffic_data['day_total']*vehicle_loss_hours['commute']['vehicle_loss_hour'])+\
                                (traffic_data['day_business']/traffic_data['day_total']*vehicle_loss_hours['business']['vehicle_loss_hour'])+\
                                (traffic_data['day_other']/traffic_data['day_total']*vehicle_loss_hours['other']['vehicle_loss_hour'])
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type
            
        if self.partofday == 'evening':
            vlh['euro_per_hour'] =(traffic_data['evening_freight']/traffic_data['evening_total']*vehicle_loss_hours['freight']['vehicle_loss_hour'])+\
                                (traffic_data['evening_commute']/traffic_data['evening_total']*vehicle_loss_hours['commute']['vehicle_loss_hour'])+\
                                (traffic_data['evening_business']/traffic_data['evening_total']*vehicle_loss_hours['business']['vehicle_loss_hour'])+\
                                (traffic_data['evening_other']/traffic_data['evening_total']*vehicle_loss_hours['other']['vehicle_loss_hour'])
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type
        vlh['euro_vlh'] = vlh['euro_per_hour'] * vlh['vlh_total']
        return vlh

    def calculate_losses_from_table(self):
        """ This function opens an existing table with traffic data and value of time to calculate losses based on detouring values. It also includes
        a traffic jam estimation.
        #TODO: check if gdf already exists from effectiveness measures.
        #TODO: If not: read feather file.
        #TODO: if yes: read gdf
        #TODO: koppelen van VVU aan de directe schade berekeningen
         """

        traffic_data = self.load_df(self.config['input'] / 'losses', 'traffic_intensities.csv')
        dict1 = {'AS_VTG': 'evening_total', 'AS_FRGT': 'evening_freight', 'AS_COMM': 'evening_commute', 'AS_BUSS': 'evening_business',
                 'AS_OTHR': 'evening_other', 'ET_FRGT': 'day_freight', 'ET_COMM': 'day_commute', 'ET_BUSS': 'day_business',
                 'ET_OTHR': 'day_other', 'ET_VTG': 'day_total', 'afstand': 'distance', 'H_Cap': 'capacity', 'H_Stroken': 'lanes'}
        traffic_data.rename(columns=dict1, inplace=True)

        detour_data = self.load_df(self.config['input'] / 'losses', 'detour_data.csv')
        dict2 = {'VA_AV_HWN': 'detour_time_evening', 'VA_RD_HWN': 'detour_time_remaining', 'VA_OS_HWN': 'detour_time_morning',
                 'VA_Etm_HWN': 'detour_time_day'}
        detour_data.rename(columns=dict2, inplace=True)

        vehicle_loss_hours = self.vehicle_loss_hours(self.config['input'] / 'losses')
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

