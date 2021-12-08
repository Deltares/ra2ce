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
from ...graph.networks_utils import graph_to_shp
from pathlib import Path


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
        detour_exist_list = []
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
                
                detour_exist_list.append(1)
            else:
                alt_dist_list.append(np.NaN)
                alt_nodes_list.append(np.NaN)
                dif_dist_list.append(np.NaN)
                detour_exist_list.append(0)

            # add edge again to the graph
            graph.add_edge(u, v, k, **data)

        # Add the new columns to the geodataframe
        gdf['alt_dist'] = alt_dist_list
        gdf['alt_nodes'] = alt_nodes_list
        gdf['diff_dist'] = dif_dist_list
        gdf['detour_exist'] = detour_exist_list

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return gdf

    def single_link_losses(self, gdf, analysis):
        """This is the function to analyse roads with a single link disruption and an alternative route.
        :param graph: graph on which to run analysis (MultiDiGraph)
        :return: df with dijkstra detour distance and path results
        """
        losses_fn = self.config['static'] / 'hazard' / analysis['loss_per_distance']
        losses_df = pd.read_excel(losses_fn, sheet_name='Sheet1')

        if analysis['loss_type'] == 'categorized':
            disruption_fn = self.config['static'] / 'hazard' / analysis['disruption_per_category']
            disruption_df = pd.read_excel(disruption_fn, sheet_name='Sheet1')
        
        if analysis['loss_type'] == 'uniform': #assume uniform threshold for disruption
            for hz in self.config['hazard_names']:            
                for col in analysis['traffic_cols'].split(","):
                    try:
                        assert gdf[col+'_detour_losses']
                        assert gdf[col+'_nodetour_losses']
                    except:
                        gdf[col+'_detour_losses'] = 0
                        gdf[col+'_nodetour_losses'] = 0
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle]  * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[(gdf['detour_exist']==1) & (gdf[hz+'_'+analysis['aggregate_wl']] > analysis['threshold']), col+'_detour_losses'] += gdf[col] * gdf['diff_dist'] * losses_df.loc[losses_df['traffic_class']==col, 'cost'].values[0] * analysis['uniform_duration'] / 24
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita_per_day[USD/person] * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[(gdf['detour_exist']==0) & (gdf[hz+'_'+analysis['aggregate_wl']] > analysis['threshold']), col+'_nodetour_losses'] += gdf[col] * losses_df.loc[losses_df['traffic_class']==col, 'occupancy'].values[0] * analysis['gdp_percapita'] * analysis['uniform_duration'] / 24
                gdf['total_losses_'+hz] = np.nansum(gdf[[x for x in gdf.columns if ('losses' in x) and (not 'total' in x)]], axis=1)

        if analysis['loss_type'] == 'categorized':
            road_classes = [x for x in disruption_df.columns if 'class' in x]
            for hz in self.config['hazard_names']:
                disruption_df['class_identifier'] = ''
                gdf['class_identifier'] = ''
                for i, road_class in enumerate(road_classes):
                    disruption_df['class_identifier'] += disruption_df[road_class]
                    gdf['class_identifier'] += gdf[road_class[6:]]
                    if i < len(road_classes)-1:
                        disruption_df['class_identifier'] += '_nextclass_'
                        gdf['class_identifier'] += '_nextclass_'

                all_road_categories = np.unique(gdf['class_identifier'])
                gdf['duration_disruption'] = 0

                for lb in np.unique(disruption_df['lower_bound']):
                    disruption_df_ = disruption_df.loc[disruption_df['lower_bound']==lb]
                    ub = disruption_df_['upper_bound'].values[0]
                    if not ub > 0:
                        ub = 1e10
                    for road_cat in all_road_categories:
                        gdf.loc[(gdf[hz+'_'+analysis['aggregate_wl']] > lb) & (gdf[hz+'_'+analysis['aggregate_wl']] <= ub) & (gdf['class_identifier'] == road_cat), 'duration_disruption'] = disruption_df_.loc[disruption_df_['class_identifier'] == road_cat, 'duration_disruption'].values[0]

                for col in analysis['traffic_cols'].split(","):
                    try:
                        assert gdf[col+'_detour_losses']
                        assert gdf[col+'_nodetour_losses']
                    except:
                        gdf[col+'_detour_losses'] = 0
                        gdf[col+'_nodetour_losses'] = 0
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[gdf['detour_exist']==1, col+'_detour_losses'] += gdf[col] * gdf['diff_dist'] * losses_df.loc[losses_df['traffic_class']==col, 'cost'].values[0] * gdf['duration_disruption'] / 24
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita[USD/person] * duration_disruption[hour] / 24[hour/day]
                    gdf.loc[gdf['detour_exist']==0, col+'_nodetour_losses'] += gdf[col] * losses_df.loc[losses_df['traffic_class']==col, 'occupancy'].values[0] * analysis['gdp_percapita'] * gdf['duration_disruption'] / 24
                gdf['total_losses_'+hz] = np.nansum(gdf[[x for x in gdf.columns if ('losses' in x) and (not 'total' in x)]], axis=1)

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
        master_graph = copy.deepcopy(graph)
        for hz in self.config['hazard_names']:
            graph = copy.deepcopy(master_graph)
            # Create a geodataframe from the full graph
            gdf = osmnx.graph_to_gdfs(master_graph, nodes=False)
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

    def multi_link_losses(self, gdf, analysis):
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
        losses_fn = self.config['static'] / 'hazard' / analysis['loss_per_distance']
        losses_df = pd.read_excel(losses_fn, sheet_name='Sheet1')

        if analysis['loss_type'] == 'categorized':
            disruption_fn = self.config['static'] / 'hazard' / analysis['disruption_per_category']
            disruption_df = pd.read_excel(disruption_fn, sheet_name='Sheet1')
            road_classes = [x for x in disruption_df.columns if 'class' in x]

        results = []
        for hz in self.config['hazard_names']:
            gdf_ = gdf.loc[gdf['hazard']==hz+'_'+analysis['aggregate_wl']].copy()
            if analysis['loss_type'] == 'uniform': #assume uniform threshold for disruption
                for col in analysis['traffic_cols'].split(","):
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    gdf_.loc[gdf_['connected']==1, col+'_losses_detour'] = gdf_[col] * gdf_['diff_dist'] * losses_df.loc[losses_df['traffic_class']==col, 'cost'].values[0] * analysis['uniform_duration'] / 24
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy_per_vehicle[person/veh] * duration_disruption[hour] / 24[hour/day] * gdp_percapita_per_day [USD/person]
                    gdf_.loc[gdf_['connected']==0, col+'_losses_nodetour'] = gdf_[col] * losses_df.loc[losses_df['traffic_class']==col, 'occupancy'].values[0] * analysis['gdp_percapita'] * analysis['uniform_duration'] / 24
                gdf_['total_losses_'+hz] = np.nansum(gdf_[[x for x in gdf_.columns if ('losses' in x) and (not 'total' in x)]], axis=1)

            if analysis['loss_type'] == 'categorized': #assume different disruption type depending on flood depth and road types
                disruption_df['class_identifier'] = ''
                gdf_['class_identifier'] = ''
                for i, road_class in enumerate(road_classes):
                    disruption_df['class_identifier'] += disruption_df[road_class]
                    gdf_['class_identifier'] += gdf_[road_class[6:]]
                    if i < len(road_classes)-1:
                        disruption_df['class_identifier'] += '_nextclass_'
                        gdf_['class_identifier'] += '_nextclass_'

                all_road_categories = np.unique(gdf_['class_identifier'])
                gdf_['duration_disruption'] = 0

                for lb in np.unique(disruption_df['lower_bound']):
                    disruption_df_ = disruption_df.loc[disruption_df['lower_bound']==lb]
                    ub = disruption_df_['upper_bound'].values[0]
                    if not ub > 0:
                        ub = 1e10
                    for road_cat in all_road_categories:
                        gdf_.loc[(gdf_[hz+'_'+analysis['aggregate_wl']] > lb) & (gdf_[hz+'_'+analysis['aggregate_wl']] <= ub) & (gdf_['class_identifier'] == road_cat), 'duration_disruption'] = disruption_df_.loc[disruption_df_['class_identifier'] == road_cat, 'duration_disruption'].values[0]

                for col in analysis['traffic_cols'].split(","):
                    # detour_losses = traffic_per_day[veh/day] * detour_distance[meter] * cost_per_meter[USD/meter/vehicle] * duration_disruption[hour] / 24[hour/day]
                    gdf_.loc[gdf_['connected']==1, col+'_losses_detour'] = gdf_[col] * gdf_['diff_dist'] * losses_df.loc[losses_df['traffic_class']==col, 'cost'].values[0] * gdf_['duration_disruption'] / 24
                    # no_detour_losses = traffic_per_day[veh/day] * occupancy[person/veh] * gdp_percapita[USD/person] * duration_disruption[hour] / 24[hour/day]
                    gdf_.loc[gdf_['connected']==0, col+'_losses_nodetour'] = gdf_[col] * losses_df.loc[losses_df['traffic_class']==col, 'occupancy'].values[0] * analysis['gdp_percapita'] * gdf_['duration_disruption'] / 24
                gdf_['total_losses_'+hz] = np.nansum(gdf_[[x for x in gdf_.columns if ('losses' in x) and (not 'total' in x)]], axis=1)
            results.append(gdf_)
            
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
            edges_remove = [e for e in graph.edges.data(keys=True) if hz+'_'+analysis['aggregate_wl'] in e[-1]]
            edges_remove = [e for e in edges_remove if
                            (e[-1][hz+'_'+analysis['aggregate_wl']] > float(analysis['threshold'])) & ('bridge' not in e[-1])]
            # to_remove = [(e[0], e[1], e[2]) for e in graph.edges.data(keys=True) if (e[-1][hz+'_'+analysis['aggregate_wl']] > float(analysis['threshold']))]
            graph_hz.remove_edges_from(edges_remove)

            # Find the routes
            od_routes = find_route_ods(graph_hz, od_nodes, analysis['weighing'])
            od_routes['hazard'] = hz+'_'+analysis['aggregate_wl']
            all_results.append(od_routes)

        all_results = pd.concat(all_results, ignore_index=True)
        return all_results

    def multi_link_origin_destination_impact(self, gdf, gdf_ori):
        """Calculates some default indicators that quantify the impacts of disruptions to origin-destination flows"""
        hazard_list = np.unique(gdf['hazard'])
        
        #calculate number of disconnected origin, destination, and origin-destination pair
        gdf['OD'] = gdf['origin'] + gdf['destination']
        gdf_ori['OD'] = gdf_ori['origin'] + gdf_ori['destination']
        init_od_pairs = len(np.unique(gdf_ori['OD']))
        init_origins = len(np.unique(gdf_ori['origin']))
        init_destinations = len(np.unique(gdf_ori['destination']))
        abs_od_disconnected = []
        share_od_disconnected = []
        abs_origin_disconnected = []
        share_origin_disconnected = []
        abs_destination_disconnected = []
        share_destination_disconnected = []
        for hz in hazard_list:
            gdf_ = gdf.loc[gdf['hazard']==hz]
            
            remaining_od_pairs = len(np.unique(gdf_['OD']))
            diff_od_pairs = init_od_pairs - remaining_od_pairs
            abs_od_disconnected.append(diff_od_pairs)
            share_od_disconnected.append(100*diff_od_pairs/init_od_pairs)
            
            remaining_origins = len(np.unique(gdf_['origin']))
            diff_origins = init_origins - remaining_origins
            abs_origin_disconnected.append(diff_origins)
            share_origin_disconnected.append(100*diff_origins/init_origins)
            
            remaining_destinations = len(np.unique(gdf_['destination']))
            diff_destinations = init_destinations - remaining_destinations
            abs_destination_disconnected.append(diff_destinations)
            share_destination_disconnected.append(100*diff_destinations/init_destinations)
            
        #calculate change in travel time/distance
        max_increase_abs = []
        min_increase_abs = []
        mean_increase_abs = []
        median_increase_abs = []
        max_increase_pc = []
        min_increase_pc = []
        mean_increase_pc = []
        median_increase_pc = []
        for hz in hazard_list:
            gdf_ = gdf.loc[gdf['hazard']==hz][['OD', 'length']]
            gdf_.columns = ['OD', 'length_'+hz]
            gdf_ori = gdf_ori.merge(gdf_, how='left', on='OD')
            gdf_ori.drop_duplicates(subset='OD', inplace=True)
            gdf_ori['diff_length_'+hz] = gdf_ori['length_'+hz] - gdf_ori['length']
            gdf_ori['diff_length_'+hz+'_pc'] = gdf_ori['diff_length_'+hz] / gdf_ori['length']
            
            max_increase_abs.append(np.nanmax(gdf_ori['diff_length_'+hz]))
            min_increase_abs.append(np.nanmin(gdf_ori['diff_length_'+hz]))
            mean_increase_abs.append(np.nanmean(gdf_ori['diff_length_'+hz]))
            median_increase_abs.append(np.nanmedian(gdf_ori['diff_length_'+hz]))
            
            max_increase_pc.append(np.nanmax(100*gdf_ori['diff_length_'+hz+'_pc']))
            min_increase_pc.append(np.nanmin(100*gdf_ori['diff_length_'+hz+'_pc']))
            mean_increase_pc.append(np.nanmean(100*gdf_ori['diff_length_'+hz+'_pc']))
            median_increase_pc.append(np.nanmedian(100*gdf_ori['diff_length_'+hz+'_pc']))
            
        diff_df = pd.DataFrame()
        diff_df['hazard'] = hazard_list
        
        diff_df['od_disconnected_abs'] = abs_od_disconnected
        diff_df['od_disconnected_pc (%)'] = share_od_disconnected
        diff_df['origin_disconnected_abs'] = abs_origin_disconnected
        diff_df['origin_disconnected_pc (%)'] = share_origin_disconnected
        diff_df['destination_disconnected_abs'] = abs_destination_disconnected
        diff_df['destination_disconnected_pc (%)'] = share_destination_disconnected
        
        diff_df['max_increase_abs'] = max_increase_abs
        diff_df['min_increase_abs'] = min_increase_abs
        diff_df['mean_increase_abs'] = mean_increase_abs
        diff_df['median_increase_abs'] = median_increase_abs
        diff_df['max_increase_pc (%)'] = max_increase_pc
        diff_df['min_increase_pc (%)'] = min_increase_pc
        diff_df['mean_increase_pc (%)'] = mean_increase_pc
        diff_df['median_increase_pc (%)'] = median_increase_pc
        
        return diff_df, gdf_ori
    
    def multi_link_origin_destination_regional_impact(self, gdf_ori):
    
        gdf_ori_ = gdf_ori.copy()
        
        #read origin points
        origin_fn = Path(self.config['static']) / 'output_graph' / 'origin_destination_table.shp'
        origin = gpd.read_file(origin_fn)
        index = [type(x)==str for x in origin['o_id']]
        origin = origin[index]
        origin.reset_index(inplace=True, drop=True)
        
        #record where each origin point resides
        origin_mapping = {}
        for o in np.unique(origin['o_id']):
            r = origin.loc[origin['o_id']==o, 'region'].values[0]
            origin_mapping.update({o : r})
        
        #record impact to each region
        origin_impact_master = pd.DataFrame()
        for r in np.unique(origin['region']):
            origin_points = list(origin.loc[origin['region']==r,'o_id'].values)
            for o in origin_points:
                origin_impact_tosave = pd.DataFrame()
                origin_impact_tosave.loc[0, 'o_id'] = o
                origin_impact_tosave.loc[0, 'region'] = r
                
                origin_impact = gdf_ori_.loc[gdf_ori_['origin'].str.contains(o)]
                
                #initial condition
                origin_impact_tosave.loc[0, 'init_length'] = np.mean(origin_impact['length'])
                origin_impact_tosave.loc[0, 'init_destination'] = len(np.unique(origin_impact['destination']))
                
                #impact of each hazard
                for col in origin_impact.columns:
                    if '_pc' in col:
                        delta = np.nanmean(origin_impact[col])
                        if not delta >= 0:
                            delta = 0
                        origin_impact_tosave.loc[0, col[12:]+'_increase'] = delta
                        
                        disconnected = origin_impact[col].isna().sum()
                        origin_impact_tosave.loc[0, col[12:]+'_disconnect'] = 100 * disconnected / origin_impact_tosave['init_destination'].values[0]
                        
                origin_impact_master = origin_impact_master.append(origin_impact_tosave)
        
        region_impact_master = origin_impact_master[origin_impact_master.columns[1:]]
        region_impact_master = region_impact_master.groupby(by='region').mean()
        
        return origin_impact_master, region_impact_master
        
    def optimal_route_origin_closest_destination(self, graph, analysis):
        crs = 4326  # TODO PUT IN DOCUMENTATION OR MAKE CHANGABLE

        base_graph = copy.deepcopy(graph)
        nx.set_edge_attributes(base_graph, 0, 'opt_cnt')

        o_name = self.config['origins_destinations']['origins_names']
        d_name = self.config['origins_destinations']['destinations_names']
        od_id = self.config['origins_destinations']['id_name_origin_destination']
        id_name = self.config['network']['file_id'] if self.config['network']['file_id'] is not None else 'ra2ce_fid'
        count_col_name = self.config['origins_destinations']['origin_count']
        weight_factor = self.config['origins_destinations']['origin_out_fraction']

        origin = load_origins(self.config)

        origin_closest_dest, other = find_closest_node_attr(graph, 'od_id', analysis['weighing'], o_name, d_name)
        pref_routes, base_graph = calc_pref_routes_closest_dest(graph, base_graph, analysis['weighing'], crs, od_id, id_name,
                                                                origin_closest_dest, origin, count_col_name,
                                                                weight_factor)

        destination = load_destinations(self.config)

        cnt_per_destination = pref_routes.groupby('destination')[['origin_cnt', 'cnt_weight']].sum().reset_index()
        for hosp, origin_cnt, cnt_weight in zip(cnt_per_destination['destination'], cnt_per_destination['origin_cnt'],
                                      cnt_per_destination['cnt_weight']):
            destination.loc[destination[od_id] == int(hosp.split('_')[-1]), 'origin_cnt'] = origin_cnt
            destination.loc[destination[od_id] == int(hosp.split('_')[-1]), 'cnt_weight'] = cnt_weight

        return base_graph, pref_routes, destination

    def multi_link_origin_closest_destination(self, graph, base_graph, destinations, analysis, opt_routes):
        unit = 'km'
        network_threshold = analysis['threshold']
        weighing = analysis['weighing']
        od_id = self.config['origins_destinations']['id_name_origin_destination']
        o_name = self.config['origins_destinations']['origins_names']
        d_name = self.config['origins_destinations']['destinations_names']
        origin_out_fraction = self.config['origins_destinations']['origin_out_fraction']
        origin_count = self.config['origins_destinations']['origin_count']

        agg_patients = pd.DataFrame(columns=['Flood map', 'Nr. people no delay', 'Nr. people delayed',
                                             'Nr. people no access', 'Total extra detour time (hours)',
                                             f'Total extra detour distance ({unit})',
                                             'Disruption by flooded road', 'Disruption by flooded destination'])

        origins = load_origins(self.config)

        threshold_destinations = 0

        # Calculate the criticality
        for hazard in self.config['hazard_names']:
            hazard_name = '_'.join([h[0] if (h.upper() != 'RP') and not h.isdecimal() else h for h in hazard.split('_')])

            # Add a column for the number of people that go to a certain destination, per flood map
            destinations[hazard_name + '_P'] = 0
            nx.set_edge_attributes(base_graph, 0, hazard_name + '_P')

            # Add a column to the neighborhoods, to indicate if they have access to any hospital
            origins[hazard_name + '_NA'] = 'access'

            # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
            h = copy.deepcopy(graph)

            edges_remove = [e for e in graph.edges.data(keys=True) if hazard+'_'+analysis['aggregate_wl'] in e[-1]]
            edges_remove = [e for e in edges_remove if
                            (e[-1][hazard+'_'+analysis['aggregate_wl']] > float(analysis['threshold'])) & ('bridge' not in e[-1])]
            h.remove_edges_from(edges_remove)

            # Find the closest hospitals
            list_closest, other = find_closest_node_attr(h, 'od_id', weighing, o_name, d_name)

            # Find the distance of the routes to the hospitals, see if those hospitals are flooded or not
            base_graph, hospitals, list_hospital_flooded, pp_no_delay, pp_delayed, extra_dist_meters, extra_miles = calc_routes_closest_dest(
                h, base_graph, list_closest, opt_routes, weighing, origins, destinations, od_id, hazard_name,
                threshold_destinations, origin_out_fraction, origin_count)

            # Calculate the number of people that cannot access any hospital
            pp_no_access = [
                origins.loc[origins[od_id] == int(oth[1].split('_')[-1]), origin_count].iloc[0] * origin_out_fraction
                if len(other) > 0 else 0 for oth in other]

            # Attribute to the neighborhoods that don't have access that they do not have any access
            if len(other) > 0:
                for oth in other:
                    origins.loc[origins[od_id] == int(oth[1].split('_')[-1]), hazard_name + '_NA'] = 'no access'

            # Now calculate for the routes that were going to a flooded destination, another non-flooded destination
            # TODO THIS PART NEEDS TO BE CHECKED AND REVISED >>>
            list_hospitals_flooded = [hosp[-1][-1] for hosp in list_hospital_flooded]

            disr_by_flood = 0

            if len(list_hospitals_flooded) > 0:
                list_nodes_to_remove = [n for n in h.nodes.data() if 'od_id' in n[-1]]
                list_nodes_to_remove = [n[0] for n in list_nodes_to_remove if n[-1]['od_id'] in list_hospitals_flooded]
                graph.remove_nodes_from(list_nodes_to_remove)

                disr_by_flood = 1
                list_closest, other = find_closest_node_attr(h, 'od_id', analysis[''], o_name, d_name)

            # The number of people that are disrupted because of a flooded road (and not because the or multiple hospitals are flooded)
            # can be calculated by adding the people without any access (this is always because of flooded roads in the first place)
            # and the people that are delayed. By subtracting the people that are disrupted by hospitals you get only the people
            # disrupted by road flooding.
            disr_by_flooded_road = round(sum(pp_no_access)) + round(sum(pp_delayed)) - disr_by_flood
            # TODO THIS PART NEEDS TO BE CHECKED AND REVISED <<<

            agg_patients = agg_patients.append(
                {'Flood map': hazard_name, 'Nr. people no delay': round(sum(pp_no_delay)),
                 'Nr. people delayed': round(sum(pp_delayed)), 'Nr. people no access': round(sum(pp_no_access)),
                 'Total extra detour time (hours)': sum(extra_dist_meters),
                 f'Total extra detour distance ({unit})': sum(extra_miles),
                 'Disruption by flooded road': disr_by_flooded_road,
                 'Disruption by flooded hospital': disr_by_flood},
                ignore_index=True)

        return base_graph, origins, agg_patients

    def execute(self):
        """Executes the indirect analysis."""
        for analysis in self.config['indirect']:
            logging.info(f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------")
            starttime = time.time()
            gdf = pd.DataFrame()
            opt_routes = None
            output_path = self.config['output'] / analysis['analysis']

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
                g_not_disrupted = nx.read_gpickle(self.config['files']['origins_destinations_graph_hazard'])
                gdf_not_disrupted = self.optimal_route_origin_destination(g_not_disrupted, analysis)
                disruption_impact_df, gdf_ori = self.multi_link_origin_destination_impact(gdf, gdf_not_disrupted)
                
                try:
                    assert self.config['origins_destinations']['region']
                    regional_impact_df, regional_impact_summary_df = self.multi_link_origin_destination_regional_impact(gdf_ori)
                    impact_csv_path = self.config['output'] / analysis['analysis'] / (analysis['name'].replace(' ', '_') + '_regional_impact.csv')
                    regional_impact_df.to_csv(impact_csv_path, index=False)
                    impact_csv_path = self.config['output'] / analysis['analysis'] / (analysis['name'].replace(' ', '_') + '_regional_impact_summary.csv')
                    regional_impact_summary_df.to_csv(impact_csv_path)
                except:
                    pass
                
                impact_csv_path = self.config['output'] / analysis['analysis'] / (analysis['name'].replace(' ', '_') + '_impact.csv')
                del gdf_ori['geometry']
                gdf_ori.to_csv(impact_csv_path, index=False)
                impact_csv_path = self.config['output'] / analysis['analysis'] / (analysis['name'].replace(' ', '_') + '_impact_summary.csv')
                disruption_impact_df.to_csv(impact_csv_path, index=False)
            elif analysis['analysis'] == 'single_link_losses':
                g = nx.read_gpickle(self.config['files']['base_graph_hazard'])
                gdf = self.single_link_redundancy(g, analysis)
                gdf = self.single_link_losses(gdf, analysis)
            elif analysis['analysis'] == 'multi_link_losses':
                g = nx.read_gpickle(self.config['files']['base_graph_hazard'])
                gdf = self.multi_link_redundancy(g, analysis)
                gdf = self.multi_link_losses(gdf, analysis)
            elif analysis['analysis'] == 'optimal_route_origin_closest_destination':
                g = nx.read_gpickle(self.config['files']['origins_destinations_graph'])
                base_graph, opt_routes, destination = self.optimal_route_origin_closest_destination(g, analysis)
                if analysis['save_shp']:
                    # TODO MAKE ONE GDF FROM RESULTS?
                    shp_path = output_path / (analysis['name'].replace(' ', '_') + '_destinations.shp')
                    save_gdf(destination, shp_path)

                    shp_path = output_path / (analysis['name'].replace(' ', '_') + '_optimal_routes.shp')
                    save_gdf(opt_routes, shp_path)

                    shp_path_nodes = output_path / (analysis['name'].replace(' ', '_') + '_results_nodes.shp')
                    shp_path_edges = output_path / (analysis['name'].replace(' ', '_') + '_results_edges.shp')
                    graph_to_shp(base_graph, shp_path_edges, shp_path_nodes)
                if analysis['save_csv']:
                    csv_path = output_path / (analysis['name'].replace(' ', '_') + '_destinations.csv')
                    del destination['geometry']
                    destination.to_csv(csv_path, index=False)

                    csv_path = output_path / (analysis['name'].replace(' ', '_') + '_optimal_routes.csv')
                    del opt_routes['geometry']
                    opt_routes.to_csv(csv_path, index=False)
            elif analysis['analysis'] == 'multi_link_origin_closest_destination':
                # TODO MAKE ONE GDF FROM RESULTS?
                g = nx.read_gpickle(self.config['files']['origins_destinations_graph_hazard'])
                base_graph, opt_routes, destination = self.optimal_route_origin_closest_destination(g, analysis)
                base_graph, origins, agg_results = self.multi_link_origin_closest_destination(g, base_graph, destination, analysis, opt_routes)
                if analysis['save_shp']:
                    shp_path = output_path / (analysis['name'].replace(' ', '_') + '_origins.shp')
                    save_gdf(origins, shp_path)

                    shp_path = output_path / (analysis['name'].replace(' ', '_') + '_destinations.shp')
                    save_gdf(destination, shp_path)

                    shp_path = output_path / (analysis['name'].replace(' ', '_') + '_optimal_routes.shp')
                    save_gdf(opt_routes, shp_path)

                    shp_path_nodes = output_path / (analysis['name'].replace(' ', '_') + '_results_nodes.shp')
                    shp_path_edges = output_path / (analysis['name'].replace(' ', '_') + '_results_edges.shp')
                    graph_to_shp(base_graph, shp_path_edges, shp_path_nodes)
                if analysis['save_csv']:
                    csv_path = output_path / (analysis['name'].replace(' ', '_') + '_destinations.csv')
                    del destination['geometry']
                    destination.to_csv(csv_path, index=False)

                    csv_path = output_path / (analysis['name'].replace(' ', '_') + '_optimal_routes.csv')
                    del opt_routes['geometry']
                    opt_routes.to_csv(csv_path, index=False)

                agg_results.to_excel(output_path / (analysis['name'].replace(' ', '_') + '_results.xlsx'))

            elif analysis['analysis'] == 'losses':

                if self.graphs['base_network_hazard'] is None:
                    gdf_in = gpd.read_feather(self.config['files']['base_network_hazard'])

                losses = Losses(self.config, analysis)
                df = losses.calculate_losses_from_table()
                gdf = gdf_in.merge(df, how='left', on='LinkNr')

            if not gdf.empty:
                # Not for all analyses a gdf is created as output.
                if analysis['save_shp']:
                    shp_path = output_path / (analysis['name'].replace(' ', '_') + '.shp')
                    save_gdf(gdf, shp_path)
                    if opt_routes:
                        shp_path = output_path / (analysis['name'].replace(' ', '_') + '_optimal_routes.shp')
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


def find_closest_node_attr(H, keyName, weighingName, originLabelContains, destLabelContains):
    """Find the closest destination node with a certain attribute from all origin nodes

    Returns:
        originClosestDest [list of tuples]: list of the origin and destination node id and node name from the routes that are found
        list_no_path [list of tuples]: list of the origin and destination node id and node name from the origins/nodes that do not have a route between them
    """
    H.add_node('special', speciallabel='special')

    special_edges = []
    for n, ndat in H.nodes.data():
        if keyName in ndat:
            if destLabelContains in ndat[keyName]:
                special_edges.append((n, 'special', {weighingName: 0}))

    H.add_edges_from(special_edges)

    list_no_path = []
    for n, ndat in H.nodes.data():
        if keyName in ndat:
            if originLabelContains in ndat[keyName]:
                if nx.has_path(H, n, 'special'):
                    path = nx.shortest_path(H, source=n, target='special', weight=weighingName)
                    ndat['closest'] = path[-2]  # Closest node with destLabelContains in keyName
                else:
                    list_no_path.append((n, ndat[keyName]))

    originClosestDest = [((nn[0], nn[-1][keyName]), (nn[-1]['closest'], H.nodes[nn[-1]['closest']][keyName])) for nn in H.nodes.data() if 'closest' in nn[-1]]
    return originClosestDest, list_no_path


def calc_pref_routes_closest_dest(graph, base_graph, weighing, crs, od_id, idName, origin_closest_dest, origins, nr_people_name, factor_hospital):
    # dataframe to save the preferred routes
    pref_routes = gpd.GeoDataFrame(columns=['o_node', 'd_node', 'origin', 'destination',
                                            'opt_path', weighing, 'match_ids', 'origin_cnt', 'cnt_weight', 'tot_miles', 'geometry'],
                                   geometry='geometry', crs='epsg:{}'.format(crs))

    # find the optimal route without (hazard) disruption
    for o, d in origin_closest_dest:
        # calculate the length of the preferred route
        pref_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=weighing)

        # save preferred route nodes
        pref_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=weighing)

        # found out which edges belong to the preferred path
        edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

        # Find the number of people per neighborhood
        nr_people_per_route_total = origins.loc[origins[od_id] == int(o[1].split('_')[-1]), nr_people_name].iloc[0]
        nr_patients_per_route = nr_people_per_route_total * factor_hospital

        pref_edges = []
        match_list = []
        length_list = []
        for u, v in edgesinpath:
            # get edge with the lowest weighing if there are multiple edges that connect u and v
            edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing])[0]
            if 'geometry' in graph[u][v][edge_key]:
                pref_edges.append(graph[u][v][edge_key]['geometry'])
            else:
                pref_edges.append(LineString([graph.nodes[u]['geometry'], graph.nodes[v]['geometry']]))
            if idName in graph[u][v][edge_key]:
                match_list.append(graph[u][v][edge_key][idName])
            if 'length' in graph[u][v][edge_key]:
                length_list.append(graph[u][v][edge_key]['length'])

            # Add the number of people that need hospital care, to the road segments. For now, each road segment in a route
            # gets attributed all the people that are taking that route.
            base_graph[u][v][edge_key]['opt_cnt'] = base_graph[u][v][edge_key]['opt_cnt'] + nr_patients_per_route

        # compile the road segments into one geometry
        pref_edges = MultiLineString(pref_edges)
        pref_routes = pref_routes.append({'o_node': o[0], 'd_node': d[0], 'origin': o[1],
                                          'destination': d[1], 'opt_path': pref_nodes,
                                          weighing: pref_route, 'match_ids': match_list,
                                          'origin_cnt': nr_people_per_route_total, 'cnt_weight': nr_patients_per_route,
                                          'tot_miles': sum(length_list) / 1609, 'geometry': pref_edges}, ignore_index=True)

    return pref_routes, base_graph


def calc_routes_closest_dest(graph, base_graph, list_closest, pref_routes, weighing, origin, dest, od_id, hazname, threshold_hospitals, factor_hospital, nr_people_name):
    pp_no_delay = [0]
    pp_delayed = [0]
    extra_weights = [0]
    extra_miles_total = [0]
    list_hospital_flooded = []

    # find the optimal route with hazard disruption
    for o, d in list_closest:
        # Check if the hospital that is accessed, is flooded
        if dest.loc[dest[od_id] == int(d[1].split('_')[-1]), hazname].iloc[0] > threshold_hospitals:
            list_hospital_flooded.append((o, d))
            continue

        # calculate the length of the preferred route
        alt_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=weighing)

        # save preferred route nodes
        alt_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=weighing)

        # Find the number of people per neighborhood
        nr_people_per_route_total = origin.loc[origin[od_id] == int(o[1].split('_')[-1]), nr_people_name].iloc[0]
        nr_patients_per_route = nr_people_per_route_total * factor_hospital

        # find out which edges belong to the preferred path
        edgesinpath = list(zip(alt_nodes[0:], alt_nodes[1:]))

        # calculate the total length of the alternative route (in miles)
        # Find the road segments that are used for the detour to the same or another hospital
        length_list = []
        for u, v in edgesinpath:
            # get edge with the lowest weighing if there are multiple edges that connect u and v
            edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing])[0]

            # Add the number of people that need hospital care, to the road segments. For now, each road segment in a route
            # gets attributed all the people that are taking that route.
            base_graph[u][v][edge_key][hazname + '_P'] = base_graph[u][v][edge_key][hazname + '_P'] + nr_patients_per_route

            if 'length' in graph[u][v][edge_key]:
                length_list.append(graph[u][v][edge_key]['length'])

        alt_dist = sum(length_list)

        # If the destination is different from the origin, the destination is further than without hazard disruption
        if pref_routes.loc[(pref_routes['origin'] == o[1]) & (pref_routes['destination'] == d[1])].empty:
            # subtract the length/time of the optimal route from the alternative route
            extra_dist = alt_route - pref_routes.loc[pref_routes['origin'] == o[1], weighing].iloc[0]
            extra_miles = alt_dist - pref_routes.loc[pref_routes['origin'] == o[1], 'tot_miles'].iloc[0]
            pp_delayed.append(nr_patients_per_route)
            extra_weights.append(extra_dist)
            extra_miles_total.append(extra_miles)
        else:
            pp_no_delay.append(nr_patients_per_route)

        # compile the road segments into one geometry
        # alt_edges = MultiLineString(alt_edges)

        # Add the number of patients to the total number of patients that go to that hospital
        dest.loc[dest[od_id] == int(d[1].split('_')[-1]), hazname + '_P'] = dest.loc[dest[od_id] == int(d[1].split('_')[-1]), hazname + '_P'].iloc[0] + nr_patients_per_route

    return base_graph, dest, list_hospital_flooded, pp_no_delay, pp_delayed, extra_weights, extra_miles_total


def load_origins(config):
    od_path = config['static'] / 'output_graph' / 'origin_destination_table.feather'
    od = gpd.read_feather(od_path)
    origin = od.loc[od['o_id'].notna()]
    del origin['d_id']
    del origin['match_ids']
    return origin


def load_destinations(config):
    od_path = config['static'] / 'output_graph' / 'origin_destination_table.feather'
    od = gpd.read_feather(od_path)
    destination = od.loc[od['d_id'].notna()]
    del destination['o_id']
    del destination['match_ids']
    return destination
